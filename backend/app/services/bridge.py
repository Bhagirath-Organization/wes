"""Execution→PR Bridge, v1 core (F10 design, decisions A1-a/A2-a/A3-a/A4).

The thin artifact-to-PR lane: an APPROVED, governed execution artifact becomes a
feature branch, an attributed commit, a verification-gated push, and an
auto-opened Pull Request — with the Founder's merge as the only exit
(PROMPT-SYS §6). Composes the existing machinery (``DevWorkspace`` sandbox,
``GitService`` git ops, ``GitHubService`` PRs, ``dev_generation``'s file-block
parser) — no new git or GitHub logic.

Sandbox hard rules (design §C-2 — each enforced mechanically and tested):
1. never the live working tree (per-run sandbox only);
2. never ATLAS paths (refusal, not skip);
3. never force-push (no force flag exists anywhere in the lane);
4. never push main (``GitService.push*`` refuses; the bridge additionally pins
   ``feature/bridge/*`` refs);
5. sandbox failure = preserve-as-evidence (no auto-clean on failure);
6. v1 has NO LLM-repair loop — any parse/apply/gate failure STOPS the bridge
   and raises the PROMPT-ESC six-field escalation; nothing is guessed.

A4 commit attribution: author = the AI employee (``Name (WES Role)
<mailbox>``), committer = the App identity, plus the machine-parseable trailers
``WES-Run:`` and ``WES-Mission:`` on every bridge commit.
"""

from __future__ import annotations

import os
import subprocess
import uuid
from dataclasses import dataclass, field

from app.core.config import get_settings

# §C-2 rule 2 — ATLAS paths the bridge REFUSES to touch (standing Founder ruling).
ATLAS_DENYLIST: tuple[str, ...] = (
    "app/api/v1/planning.py",
    "app/api/v1/engineering.py",
    "app/services/execution_planning.py",
    "app/services/engineering_execution.py",
    "app/models/planning.py",
    "app/models/engineering.py",
    "alembic/versions/0030_autonomous_planning_atlas.py",
    "alembic/versions/0031_autonomous_engineering_atlas.py",
)

BRANCH_PREFIX = "feature/bridge/"


class BridgeEscalation(Exception):
    """v1 no-repair rule: the bridge stops here and the Founder gets the
    PROMPT-ESC six-field package. Never a guess, never a retry."""

    def __init__(self, message: str, escalation: str):
        super().__init__(message)
        self.escalation = escalation


@dataclass
class BridgeResult:
    status: str  # opened | escalated
    branch: str | None = None
    head_sha: str | None = None
    pr_number: int | None = None
    pr_url: str | None = None
    files: list[str] = field(default_factory=list)
    sandbox_path: str | None = None  # preserved on failure (rule 5)
    escalation: str | None = None


def _six_fields(issue: str, evidence: str, options: str, recommendation: str) -> str:
    return (
        "ESCALATION — execution→PR bridge stopped (v1 no-repair rule).\n"
        f"1. Issue: {issue}\n"
        "2. Severity: high — the approved artifact did not become a PR; nothing was pushed.\n"
        f"3. Evidence: {evidence}\n"
        f"4. Options considered: {options}\n"
        f"5. Recommendation: {recommendation}\n"
        "6. Expected outcome: Founder decides; the bridge re-runs only on an amended "
        "artifact or instruction — it never repairs or guesses (design §C-2.6)."
    )


class ExecutionPRBridge:
    """One bridge run: approved artifact → attributed commit → gated PR."""

    def __init__(
        self,
        *,
        run_id: uuid.UUID,
        mission_id: uuid.UUID,
        author_name: str,
        author_role: str,
        gate=None,
        pr_opener=None,
        workspace=None,
        repo_subdir: str | None = None,
        collect_check=None,
    ):
        self.run_id = run_id
        self.mission_id = mission_id
        self.author_name = author_name
        self.author_role = author_role
        # F17: the app root under the clone (WES nests it under ``backend/``).
        self.repo_subdir = (
            repo_subdir if repo_subdir is not None else get_settings().bridge_repo_subdir
        )
        # F18: returns the set of collected pytest node paths for a gated tree, so
        # the bridge can PROVE the artifact's tests actually ran. Injected in tests;
        # the default shells out to ``pytest --collect-only`` (see _collected_nodes).
        self._collect_check = collect_check or self._collected_nodes
        # A3-a gate: callable(sandbox_path) -> (ok: bool, report: str). The
        # default runs the full suite + coverage floor in the sandbox; tests
        # inject a stub. Injection keeps PR-1 unit-testable without a container.
        self._gate = gate or self._default_gate
        # A2-a: PR auto-open via the App. Injectable for tests.
        self._pr_opener = pr_opener
        self._workspace = workspace

    # -- §C-2 rule 1: the sandbox ------------------------------------------

    def _make_sandbox(self, task_code: str) -> str:
        from app.services.dev_git import DevWorkspace

        ws = self._workspace or DevWorkspace()
        path = os.path.abspath(ws.create(task_code))
        live_tree = os.path.abspath(get_settings().bridge_live_tree_guard or "/opt/wes-green")
        if path == live_tree or path.startswith(live_tree + os.sep):
            raise BridgeEscalation(
                "sandbox path resolves inside the live working tree",
                _six_fields(
                    "sandbox path resolved inside the protected live working tree",
                    f"sandbox={path} live_tree={live_tree}",
                    "(a) fix bridge sandbox base configuration; (b) halt bridge use",
                    "fix configuration; the guard refused before any write",
                ),
            )
        return path

    # -- B1: parse (reuses the existing file-block protocol) ---------------

    def parse_artifact(self, artifact_text: str) -> list:
        from app.services.dev_generation import _parse_changes

        changes = _parse_changes(artifact_text, "bridge", "bridge artifact")
        if not changes:
            raise BridgeEscalation(
                "artifact contains no parseable file blocks",
                _six_fields(
                    "the approved artifact contains no parseable file blocks "
                    "(<<<FILE: path>>> protocol or labelled fences)",
                    f"artifact length={len(artifact_text)} chars; parser found 0 changes",
                    "(a) author re-issues the artifact with file blocks; "
                    "(b) task returns to Engineering",
                    "return to the authoring employee with the protocol reminder",
                ),
            )
        # §C-2 rule 2: ATLAS refusal — before anything is written anywhere.
        touched = [c.path for c in changes]
        forbidden = [p for p in touched if self._is_atlas_path(p)]
        if forbidden:
            raise BridgeEscalation(
                f"artifact touches protected ATLAS paths: {forbidden}",
                _six_fields(
                    f"the artifact writes protected ATLAS paths {forbidden} (standing ruling)",
                    f"denylist match on {len(forbidden)} of {len(touched)} files",
                    "(a) descope the ATLAS files from the task; (b) Founder lifts the "
                    "ruling explicitly (separate decision)",
                    "refuse — the ruling stands until the Founder says otherwise",
                ),
            )
        return changes

    @staticmethod
    def _is_atlas_path(path: str) -> bool:
        # Strip only a literal "./" prefix — lstrip("./") would eat the leading
        # dot of dotfiles like ".s5.txt" and blind the denylist.
        norm = path[2:] if path.startswith("./") else path
        base = os.path.basename(norm)
        return (
            any(norm.endswith(p) or norm == p for p in ATLAS_DENYLIST)
            or (base.startswith(".s") and base[2:3].isdigit() and base.endswith(".txt"))
        )

    # -- B2 + A4: apply and commit with attribution ------------------------

    def _apply_and_commit(self, git, changes, task_code: str, title: str) -> str:
        from app.services.dev_git import SandboxError

        branch = f"{BRANCH_PREFIX}{task_code.lower()}"
        git.create_branch(branch)
        for change in changes:
            # F17: artifact paths are app-root-relative; write them under the
            # configured repo subdir so they land in the tree the gate runs in.
            rel = os.path.join(self.repo_subdir, change.path) if self.repo_subdir else change.path
            target = git._assert_within(rel)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w", encoding="utf-8") as fh:
                fh.write(change.content)
        s = get_settings()
        author_email = s.bridge_author_mailbox_pattern.format(
            employee=self.author_name.lower().replace(" ", "-")
        )
        message = (
            f"{title}\n\n"
            f"Bridge-authored change from the approved execution artifact.\n\n"
            f"WES-Run: {self.run_id}\n"
            f"WES-Mission: {self.mission_id}\n"
        )
        env = {
            **os.environ,
            "GIT_AUTHOR_NAME": f"{self.author_name} (WES {self.author_role})",
            "GIT_AUTHOR_EMAIL": author_email,
            "GIT_COMMITTER_NAME": s.bridge_committer_name,
            "GIT_COMMITTER_EMAIL": s.bridge_committer_email,
            "GIT_TERMINAL_PROMPT": "0",
        }
        subprocess.run(["git", "add", "-A"], cwd=git.path, check=True, capture_output=True)
        proc = subprocess.run(
            ["git", "commit", "-q", "-m", message],
            cwd=git.path, env=env, capture_output=True, text=True,
        )
        if proc.returncode != 0:
            raise SandboxError(f"bridge commit failed: {proc.stderr.strip()[:300]}")
        return branch

    # -- F17/F18: the artifact must land in, and be tested by, the gated tree ---

    @staticmethod
    def _is_test_path(path: str) -> bool:
        return (
            path.startswith("tests/")
            or "/tests/" in path
            or os.path.basename(path).startswith("test_")
        )

    def _gated_root(self, sandbox: str) -> str:
        return os.path.join(sandbox, self.repo_subdir) if self.repo_subdir else sandbox

    def _collected_nodes(self, gated_root: str) -> set[str]:
        """Paths of every test file pytest collects in ``gated_root`` (hermetic)."""
        env = {k: v for k, v in os.environ.items() if not k.startswith("WES_")}
        proc = subprocess.run(
            ["python", "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"],
            cwd=gated_root, env=env, capture_output=True, text=True, timeout=600,
        )
        nodes = set()
        for line in (proc.stdout or "").splitlines():
            node = line.split("::", 1)[0].strip()
            if node.endswith(".py"):
                nodes.add(node)
        return nodes

    def _verify_gated(self, sandbox: str, changes: list) -> None:
        """F17/F18: refuse unless every changed file lands in the gated tree AND
        the artifact's own test file is actually collected by the gate — so a
        false-green (an artifact the suite never touched) is impossible."""
        gated_root = self._gated_root(sandbox)
        missing = [c.path for c in changes if not os.path.isfile(os.path.join(gated_root, c.path))]
        if missing:
            raise BridgeEscalation(
                f"changed files are not inside the gated tree: {missing}",
                _six_fields(
                    f"artifact files {missing} did not land under the gated tree "
                    f"({self.repo_subdir or '<clone root>'}) — the gate cannot test them (F17)",
                    f"gated_root={gated_root}; repo_subdir={self.repo_subdir!r}",
                    "(a) fix bridge_repo_subdir for this repo; (b) fix the artifact paths",
                    "refuse — a change the gate cannot see must never open a PR",
                ),
            )
        test_files = [c.path for c in changes if self._is_test_path(c.path)]
        if not test_files:
            raise BridgeEscalation(
                "artifact ships no test the gate can run",
                _six_fields(
                    "the artifact changes code but ships no test file — the gate cannot "
                    "validate the change (SOP-TESTING; F18)",
                    f"changed files: {[c.path for c in changes]}",
                    "(a) author adds tests; (b) task returns to Engineering",
                    "refuse — code without a runnable test is not a verifiable change",
                ),
            )
        collected = self._collect_check(gated_root)
        not_collected = [
            t for t in test_files if not any(node.endswith(t) or node == t for node in collected)
        ]
        if not_collected:
            raise BridgeEscalation(
                f"artifact tests are not collected by the gate: {not_collected}",
                _six_fields(
                    f"the artifact's test files {not_collected} are NOT in the gate's "
                    "collection — the gate would pass without running them (F18 false-green)",
                    f"collected {len(collected)} test files in {gated_root}",
                    "(a) fix the test path/location; (b) fix bridge_repo_subdir",
                    "refuse — a green gate that never ran the change's tests is a lie",
                ),
            )

    # -- A3-a: the gate ----------------------------------------------------

    def _default_gate(self, sandbox_path: str) -> tuple[bool, str]:
        """Full suite + coverage floor inside the gated tree."""
        env = {k: v for k, v in os.environ.items() if not k.startswith("WES_")}
        proc = subprocess.run(
            ["python", "-m", "pytest", "-q", "--cov=app",
             f"--cov-fail-under={get_settings().bridge_coverage_floor}",
             "-p", "no:cacheprovider"],
            cwd=self._gated_root(sandbox_path), env=env,
            capture_output=True, text=True, timeout=1800,
        )
        tail = (proc.stdout or "")[-2000:]
        return proc.returncode == 0, tail

    # -- the run -----------------------------------------------------------

    def run(self, *, artifact_text: str, task_code: str, title: str, git=None) -> BridgeResult:
        """B1→B4. Raises BridgeEscalation per §C-2.6; preserves the sandbox on
        failure per §C-2.5 (the caller reports its path — never auto-cleaned)."""
        changes = self.parse_artifact(artifact_text)  # B1 (+ ATLAS refusal)
        sandbox = self._make_sandbox(task_code)  # rule 1
        try:
            if git is None:
                from app.services.dev_git import GitService

                git = GitService(sandbox)
                git.init()
            branch = self._apply_and_commit(git, changes, task_code, title)  # B2 + A4
            if not branch.startswith(BRANCH_PREFIX):  # rule 4 (belt over GitService's braces)
                raise BridgeEscalation(
                    f"refusing non-bridge ref {branch!r}",
                    _six_fields(
                        f"bridge produced a non-bridge ref {branch!r}",
                        f"expected prefix {BRANCH_PREFIX!r}",
                        "(a) fix the branch naming; (b) halt",
                        "fix naming; nothing was pushed",
                    ),
                )
            self._verify_gated(sandbox, changes)  # F17/F18: artifact is in + tested by the gated tree
            ok, report = self._gate(sandbox)  # B3
            if not ok:
                raise BridgeEscalation(
                    "verification gate failed",
                    _six_fields(
                        "the verification gate (full suite + coverage floor) failed",
                        f"sandbox preserved at {sandbox}; gate tail: {report[-400:]}",
                        "(a) task returns to Engineering with the gate output; "
                        "(b) author amends the artifact",
                        "return to Engineering — a failing gate is a valid, honest outcome",
                    ),
                )
            pr = self._open_pr(git, branch, task_code, title)  # B4 (A2-a)
            return BridgeResult(
                status="opened", branch=branch, head_sha=git.head_sha(),
                pr_number=pr.get("number"), pr_url=pr.get("url"),
                files=[c.path for c in changes], sandbox_path=sandbox,
            )
        except BridgeEscalation as exc:
            # Rule 5: the sandbox is preserved exactly as it failed.
            raise BridgeEscalation(
                str(exc), exc.escalation + f"\n[sandbox preserved: {sandbox}]"
            ) from exc

    def _open_pr(self, git, branch: str, task_code: str, title: str) -> dict:
        if self._pr_opener is not None:
            return self._pr_opener(git=git, branch=branch, task_code=task_code, title=title)
        from app.services.github_service import GitHubService

        gh = GitHubService()
        token = gh._installation_token()  # App-internal client; same trust domain
        git.push_via_app(token, get_settings().github_repo, branch)
        body = (
            f"Bridge-opened PR from the approved execution artifact.\n\n"
            f"WES-Run: {self.run_id}\nWES-Mission: {self.mission_id}\n\n"
            "Merge decision is the Founder's (PROMPT-SYS §6)."
        )
        data = gh.create_pull_request(
            title=title, head=branch, base=get_settings().github_default_branch, body=body
        )
        return {"number": data.get("number"), "url": data.get("html_url")}

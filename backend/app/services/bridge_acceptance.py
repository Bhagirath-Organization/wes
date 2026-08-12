"""F10-PR-3 — the live bridge cycle (design §D acceptance run).

``LiveBridgeRunner`` drives one REAL end-to-end bridge cycle: it clones the
target repository, then runs :class:`~app.services.bridge.ExecutionPRBridge`
with the clone as its sandbox and a **real** gate (the full test suite executed
inside the clone). On success a machine-authored, A4-attributed PR is opened on
the target repo; the Founder's merge remains the only exit.

The runner is thin composition — it adds a clone step and a real pytest gate and
reuses every guarantee the bridge core already proved (parse, ATLAS refusal,
attribution, no-repair escalation). Clone / gate / PR are all injectable so the
unit tests exercise the wiring without network or a container; the real run
supplies the live implementations.
"""

from __future__ import annotations

import os
import subprocess
import uuid

from app.core.config import get_settings
from app.services.bridge import BridgeResult, ExecutionPRBridge


class _FixedWorkspace:
    """A workspace whose ``create`` returns an already-prepared path (the clone).

    Lets the bridge use the clone as its sandbox: sandbox == git working tree,
    so the gate runs the real suite against the artifact-in-context.
    """

    def __init__(self, path: str):
        self._path = path

    def create(self, task_code: str) -> str:  # noqa: ARG002 - signature parity
        return self._path


class LiveBridgeRunner:
    def __init__(
        self,
        *,
        run_id: uuid.UUID,
        mission_id: uuid.UUID,
        author_name: str,
        author_role: str,
        repo: str,
        base: str = "main",
        cloner=None,
        gate=None,
    ):
        self.run_id = run_id
        self.mission_id = mission_id
        self.author_name = author_name
        self.author_role = author_role
        self.repo = repo
        self.base = base
        self._cloner = cloner or self._real_clone
        self._gate = gate or self._real_gate

    # -- real implementations (injected out in tests) ----------------------

    def _real_clone(self, token: str, task_code: str) -> str:
        """Shallow-clone the target repo via the App token into a fresh sandbox."""
        import tempfile

        sandbox = tempfile.mkdtemp(prefix=f"wes-bridge-{task_code.lower()}-")
        path = os.path.join(sandbox, "repo")
        url = f"https://x-access-token:{token}@github.com/{self.repo}.git"
        proc = subprocess.run(
            ["git", "clone", "--depth", "1", "-b", self.base, url, path],
            capture_output=True, text=True, timeout=300,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"clone failed: {proc.stderr.strip()[:300]}")
        return path

    @staticmethod
    def _hermetic_env() -> dict:
        """F16: the gate must run HERMETICALLY — the suite's own fixtures (an
        in-memory SQLite DB, mock providers), never production infrastructure.

        The runner needs the GitHub App config in its own environment (to push
        and open the PR), but that config also carries ``WES_DATABASE_URL`` (host
        ``db``) and provider credentials. Left in the gate's environment they make
        DB/credential-touching tests attempt REAL connections — which errored the
        acceptance gate off-network, and (worse) could have run tests against the
        production database on-network. Stripping every ``WES_``-prefixed variable
        reproduces exactly the keyless condition under which the suite is green
        (the app falls back to its test defaults).
        """
        return {k: v for k, v in os.environ.items() if not k.startswith("WES_")}

    def _real_gate(self, sandbox: str) -> tuple[bool, str]:
        """A3-a: full suite + coverage floor inside the cloned checkout, hermetic."""
        proc = subprocess.run(
            ["python", "-m", "pytest", "-q", "--cov=app",
             f"--cov-fail-under={get_settings().bridge_coverage_floor}",
             "-p", "no:cacheprovider"],
            cwd=os.path.join(sandbox, "backend"),
            env=self._hermetic_env(),
            capture_output=True, text=True, timeout=1800,
        )
        return proc.returncode == 0, (proc.stdout or "")[-2000:]

    # -- the live cycle ----------------------------------------------------

    def run(self, *, artifact_text: str, task_code: str, title: str, token: str) -> BridgeResult:
        from app.services.dev_git import GitService

        clone_path = self._cloner(token, task_code)
        git = GitService(clone_path)  # already a git repo — no init
        bridge = ExecutionPRBridge(
            run_id=self.run_id,
            mission_id=self.mission_id,
            author_name=self.author_name,
            author_role=self.author_role,
            gate=self._gate,
            workspace=_FixedWorkspace(clone_path),
            # A2-a: real PR via the bridge's default _open_pr (push_via_app + PR),
            # but on the runner's explicit repo (not the ambient github_repo).
            pr_opener=self._open_pr_on_repo,
        )
        return bridge.run(artifact_text=artifact_text, task_code=task_code, title=title, git=git)

    def _open_pr_on_repo(self, *, git, branch: str, task_code: str, title: str) -> dict:
        from app.services.github_service import GitHubService

        gh = GitHubService(repo=self.repo)
        token = gh._installation_token()
        git.push_via_app(token, self.repo, branch)
        body = (
            "Machine-authored by the WES execution→PR bridge (F10) from an approved "
            "execution artifact.\n\n"
            f"WES-Run: {self.run_id}\nWES-Mission: {self.mission_id}\n\n"
            "Author of the commit is the AI employee; committer is the App identity "
            "(A4). Merge decision is the Founder's (PROMPT-SYS §6)."
        )
        data = gh.create_pull_request(title=title, head=branch, base=self.base, body=body)
        return {"number": data.get("number"), "url": data.get("html_url")}

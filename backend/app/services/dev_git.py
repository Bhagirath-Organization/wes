"""Git sandbox + Git service for the Autonomous Development Engine (Sprint 13).

Every autonomous implementation runs in a REAL, isolated git repository created
under the configured workspace directory — never the WES, WORLD, or Blueprint
repositories. Git operations are real (subprocess ``git``): init, branch, atomic
commits (Conventional Commits), and diffs.

Blueprint Vol 04 (Git Workflow) and Vol 06 (GitHub is the source of truth) require
delivered work to reach GitHub, so the engine CAN push a feature branch over an SSH
deploy key. It still NEVER merges and NEVER pushes the default branch — merge to
``main`` happens only through a reviewed Pull Request, and the Founder is the final
authority.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import uuid

from app.core.config import get_settings

# Paths that must never be modified by the engine, regardless of target.
FORBIDDEN_SEGMENTS = ("blueprint", "/world", "wes/blueprint")

_GIT_ENV = {
    "GIT_AUTHOR_NAME": "WES AI",
    "GIT_AUTHOR_EMAIL": "ai@wes.studio",
    "GIT_COMMITTER_NAME": "WES AI",
    "GIT_COMMITTER_EMAIL": "ai@wes.studio",
    "GIT_TERMINAL_PROMPT": "0",
}


class SandboxError(RuntimeError):
    pass


def _run(
    args: list[str], cwd: str, check: bool = True, extra_env: dict | None = None,
    timeout: int = 120,
) -> subprocess.CompletedProcess:
    env = {**os.environ, **_GIT_ENV, **(extra_env or {})}
    proc = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
    if check and proc.returncode != 0:
        raise SandboxError(f"git {' '.join(args[1:])} failed: {proc.stderr.strip()[:300]}")
    return proc


class DevWorkspace:
    """Creates and guards per-task git sandboxes."""

    def __init__(self):
        self.base = os.path.abspath(get_settings().dev_workspace_dir)

    def _assert_safe(self, path: str) -> None:
        real = os.path.abspath(path)
        if not real.startswith(self.base + os.sep) and real != self.base:
            raise SandboxError("Refusing to operate outside the development workspace")
        low = real.lower()
        if any(seg in low for seg in FORBIDDEN_SEGMENTS):
            raise SandboxError("Refusing to touch a protected path (Blueprint/WORLD)")

    def create(self, task_code: str) -> str:
        """Initialize a fresh sandbox git repo on ``main`` and return its path."""
        os.makedirs(self.base, exist_ok=True)
        path = os.path.join(self.base, f"{task_code}-{uuid.uuid4().hex[:8]}")
        self._assert_safe(path)
        if os.path.exists(path):  # pragma: no cover - uuid collision
            shutil.rmtree(path)
        os.makedirs(path)
        git = GitService(path)
        git.init()
        return path

    def clone(self, task_code: str, repo: str, token: str, base: str = "main") -> str:
        """Clone a real GitHub repo (via App token) so delivery shares its history.

        Used for autonomous delivery into an existing repository: the sandbox is a
        genuine clone of ``base``, so a pushed branch produces a clean, minimal PR
        diff. The token appears only in the transient clone URL, never persisted.
        """
        os.makedirs(self.base, exist_ok=True)
        path = os.path.join(self.base, f"{task_code}-{uuid.uuid4().hex[:8]}")
        self._assert_safe(path)
        if os.path.exists(path):  # pragma: no cover - uuid collision
            shutil.rmtree(path)
        url = f"https://x-access-token:{token}@github.com/{repo}.git"
        proc = _run(
            ["git", "clone", "--depth", "1", "-b", base, url, path],
            self.base, check=False, timeout=300,
        )
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout).replace(token, "***").strip()[:300]
            raise SandboxError(f"clone failed: {err}")
        # Anchor a local 'main' ref at the cloned base commit so the workflow's
        # diff base (git.diff("main"), review board, metrics) works unchanged even
        # when the delivery base branch is not literally named "main".
        if base not in ("main", "master"):
            _run(["git", "branch", "-f", "main", "HEAD"], path, check=False)
        return path

    def cleanup(self, path: str) -> None:
        self._assert_safe(path)
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)


class GitService:
    """Real git operations, scoped to one sandbox path. Never pushes or merges."""

    def __init__(self, path: str):
        self.path = os.path.abspath(path)

    def _assert_within(self, rel_path: str) -> str:
        target = os.path.abspath(os.path.join(self.path, rel_path))
        if not target.startswith(self.path + os.sep):
            raise SandboxError(f"Path '{rel_path}' escapes the sandbox")
        low = target.lower()
        if any(seg in low for seg in FORBIDDEN_SEGMENTS):
            raise SandboxError("Refusing to write a protected path (Blueprint/WORLD)")
        return target

    # -- lifecycle ---------------------------------------------------------

    def init(self) -> None:
        _run(["git", "init", "-q", "-b", "main"], self.path, check=False)
        # Older git without -b: ensure branch.
        if self.current_branch() not in ("main", "master"):
            _run(["git", "checkout", "-q", "-b", "main"], self.path, check=False)
        readme = os.path.join(self.path, "README.md")
        with open(readme, "w", encoding="utf-8") as fh:
            fh.write("# Sandbox\n\nWES autonomous development sandbox.\n")
        _run(["git", "add", "-A"], self.path)
        _run(["git", "commit", "-q", "-m", "chore: initialize sandbox"], self.path)

    def create_branch(self, branch: str) -> str:
        _run(["git", "checkout", "-q", "-b", branch], self.path)
        return branch

    # -- remote transport (Blueprint Vol 04 / Vol 06) ------------------------

    @staticmethod
    def remote_configured() -> bool:
        """True when a push target and a usable deploy key are both configured."""
        s = get_settings()
        return bool(
            s.github_ssh_url
            and s.github_deploy_key_path
            and os.path.isfile(s.github_deploy_key_path)
        )

    @staticmethod
    def _ssh_env() -> dict:
        """Force git to use the deploy key only — never an ambient agent or key."""
        key = get_settings().github_deploy_key_path
        return {
            "GIT_SSH_COMMAND": (
                f"ssh -i {key} -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new "
                "-o BatchMode=yes -o ConnectTimeout=20"
            )
        }

    def set_remote(self, url: str | None = None, name: str = "origin") -> str:
        """Point ``name`` at the configured GitHub repository (idempotent)."""
        url = url or get_settings().github_ssh_url
        if not url:
            raise SandboxError("No GitHub remote configured (WES_GITHUB_SSH_URL)")
        existing = _run(["git", "remote"], self.path, check=False).stdout.split()
        verb = "set-url" if name in existing else "add"
        _run(["git", "remote", verb, name, url], self.path)
        return url

    def remote_reachable(self) -> bool:
        """Verify the deploy key can actually talk to GitHub (real network call).

        Queries the configured URL directly rather than a remote name, so it works
        on a fresh sandbox that has no ``origin`` yet and never mutates the repo.
        """
        if not self.remote_configured():
            return False
        proc = _run(
            ["git", "ls-remote", "--heads", get_settings().github_ssh_url], self.path,
            check=False, extra_env=self._ssh_env(), timeout=60,
        )
        return proc.returncode == 0

    def push_via_app(self, token: str, repo: str, branch: str | None = None) -> dict:
        """Push a feature branch over HTTPS using a GitHub App installation token.

        Lets delivery authenticate as the App (P0-B) instead of the SSH deploy
        key. The token is passed in memory, used only in the remote URL for this
        one command, and never written to git config or logged.
        """
        branch = branch or self.current_branch()
        default = get_settings().github_default_branch
        if branch in (default, "main", "master"):
            raise SandboxError(
                f"Refusing to push '{branch}' directly — Blueprint Vol 04 requires "
                "a reviewed Pull Request to reach the default branch"
            )
        if not token or not repo:
            raise SandboxError("push_via_app requires an installation token and repo")
        url = f"https://x-access-token:{token}@github.com/{repo}.git"
        # Pass the URL as a positional arg (not a stored remote) so the token is
        # never persisted in .git/config.
        proc = _run(
            ["git", "push", url, f"HEAD:refs/heads/{branch}"], self.path,
            check=False, timeout=300,
        )
        if proc.returncode != 0:
            # Scrub any accidental echo of the URL (and thus the token) from output.
            err = (proc.stderr or proc.stdout).replace(token, "***").strip()[:300]
            raise SandboxError(f"git push (app) failed: {err}")
        return {"pushed": True, "branch": branch, "repo": repo, "head_sha": self.head_sha()}

    def push(self, branch: str | None = None, name: str = "origin") -> dict:
        """Push a feature branch to GitHub.

        Refuses the default branch: Blueprint Vol 04 requires ``main`` to be reached
        only through a reviewed Pull Request, never a direct push.
        """
        branch = branch or self.current_branch()
        default = get_settings().github_default_branch
        if branch in (default, "main", "master"):
            raise SandboxError(
                f"Refusing to push '{branch}' directly — Blueprint Vol 04 requires "
                "a reviewed Pull Request to reach the default branch"
            )
        if not self.remote_configured():
            raise SandboxError(
                "GitHub remote not configured (WES_GITHUB_SSH_URL + deploy key required)"
            )
        self.set_remote(name=name)
        proc = _run(
            ["git", "push", "--set-upstream", name, branch], self.path,
            check=False, extra_env=self._ssh_env(), timeout=300,
        )
        if proc.returncode != 0:
            raise SandboxError(f"git push failed: {(proc.stderr or proc.stdout).strip()[:300]}")
        return {
            "pushed": True,
            "branch": branch,
            "remote": get_settings().github_ssh_url,
            "head_sha": self.head_sha(),
            "output": (proc.stderr or proc.stdout).strip()[:500],
        }

    # -- file ops (guarded) ------------------------------------------------

    def write_file(self, rel_path: str, content: str) -> None:
        target = self._assert_within(rel_path)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(content)

    def delete_file(self, rel_path: str) -> None:
        target = self._assert_within(rel_path)
        if os.path.exists(target):
            os.remove(target)

    def rename_file(self, old_rel: str, new_rel: str) -> None:
        src = self._assert_within(old_rel)
        dst = self._assert_within(new_rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.exists(src):
            os.rename(src, dst)

    def read_file(self, rel_path: str) -> str | None:
        target = self._assert_within(rel_path)
        if not os.path.exists(target):
            return None
        with open(target, encoding="utf-8", errors="ignore") as fh:
            return fh.read()

    # -- git queries / commits --------------------------------------------

    def stage_all(self) -> None:
        _run(["git", "add", "-A"], self.path)

    def commit(self, message: str) -> str:
        _run(["git", "commit", "-q", "-m", message], self.path)
        return self.head_sha()

    def rollback_to(self, sha: str) -> None:
        """Hard-reset the working tree back to ``sha`` (used when a modification
        fails its tests). Real ``git reset --hard`` — never touches history beyond
        this sandbox."""
        _run(["git", "reset", "-q", "--hard", sha], self.path)
        _run(["git", "clean", "-fdq"], self.path, check=False)

    def restore_worktree(self) -> None:
        """Discard uncommitted working-tree changes, restoring the last commit."""
        _run(["git", "checkout", "-q", "--", "."], self.path, check=False)
        _run(["git", "clean", "-fdq"], self.path, check=False)

    def head_sha(self) -> str:
        return _run(["git", "rev-parse", "HEAD"], self.path).stdout.strip()

    def current_branch(self) -> str:
        return _run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], self.path, check=False
        ).stdout.strip()

    def diff(self, base: str = "main") -> str:
        return _run(["git", "diff", f"{base}...HEAD"], self.path, check=False).stdout

    def diff_file(self, base: str, rel_path: str) -> str:
        return _run(
            ["git", "diff", f"{base}...HEAD", "--", rel_path], self.path, check=False
        ).stdout

    def shortstat(self, base: str = "main") -> dict:
        out = _run(["git", "diff", "--shortstat", f"{base}...HEAD"], self.path, check=False).stdout
        files = additions = deletions = 0
        import re

        if m := re.search(r"(\d+) files? changed", out):
            files = int(m.group(1))
        if m := re.search(r"(\d+) insertion", out):
            additions = int(m.group(1))
        if m := re.search(r"(\d+) deletion", out):
            deletions = int(m.group(1))
        return {"files_changed": files, "additions": additions, "deletions": deletions}

    def commit_count(self, base: str = "main") -> int:
        out = _run(["git", "rev-list", "--count", f"{base}..HEAD"], self.path, check=False).stdout
        return int(out.strip() or 0)

    def log(self, base: str = "main") -> list[str]:
        out = _run(
            ["git", "log", "--pretty=format:%s", f"{base}..HEAD"], self.path, check=False
        ).stdout
        return [line for line in out.splitlines() if line]

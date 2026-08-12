"""GitHubService — GitHub REST API operations authenticated as a GitHub App (P0-B).

Blueprint Vol 04 (Git Workflow: PR → review → merge) and Vol 06 (GitHub is the
source of truth) require WES to drive Pull Requests, merges, and repositories on
GitHub. This service owns ONLY the REST API surface; git transport (branch,
commit, push) stays in ``GitService`` and is reused unchanged.

Authentication follows GitHub's official App model:

    RS256 JWT (signed with the App private key, ≤10 min)
        → POST /app/installations/{id}/access_tokens
        → installation access token (~1 h), cached and auto-refreshed.

Security invariants:
* The private key is read only from ``github_app_private_key_path`` — never the
  repository, never the database.
* The JWT and the installation token are NEVER logged or returned to callers.
* No credential is ever persisted; the token cache is in-memory only.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import httpx
import jwt

from app.core.config import get_settings

_API = "https://api.github.com"
_JWT_TTL = 540          # 9 min — under GitHub's 10-min ceiling, clock-skew safe
_REFRESH_SKEW = 60      # refresh the installation token this many seconds early


class GitHubError(RuntimeError):
    """A GitHub REST operation failed. Messages never contain credentials."""


@dataclass
class _CachedToken:
    token: str
    expires_at: float  # epoch seconds


# Module-level cache keyed by installation id, so a token is reused across
# service instances until it nears expiry. In-memory only — never persisted.
_TOKEN_CACHE: dict[str, _CachedToken] = {}


class GitHubService:
    """Thin, App-authenticated client for the GitHub REST API."""

    def __init__(self, repo: str | None = None):
        s = get_settings()
        self.app_id = s.github_app_id
        self.installation_id = s.github_app_installation_id
        self.key_path = s.github_app_private_key_path
        self.repo = repo or s.github_repo  # "owner/name"

    # -- configuration -----------------------------------------------------

    @staticmethod
    def configured() -> bool:
        s = get_settings()
        import os

        return bool(
            s.github_app_id
            and s.github_app_installation_id
            and s.github_app_private_key_path
            and os.path.isfile(s.github_app_private_key_path)
        )

    def _require(self) -> None:
        if not self.configured():
            raise GitHubError("GitHub App is not configured")

    # -- authentication (never logs the JWT or the token) ------------------

    def _app_jwt(self) -> str:
        """Build a short-lived RS256 JWT signed with the App private key."""
        with open(self.key_path, "r", encoding="utf-8") as fh:
            key = fh.read()
        now = int(time.time())
        payload = {"iat": now - 60, "exp": now + _JWT_TTL, "iss": self.app_id}
        return jwt.encode(payload, key, algorithm="RS256")

    def _installation_token(self) -> str:
        """Return a valid installation token, refreshing it before expiry.

        The token is cached in-memory per installation and reused until it is
        within ``_REFRESH_SKEW`` seconds of expiry, at which point it is renewed.
        """
        self._require()
        cached = _TOKEN_CACHE.get(self.installation_id)
        if cached and cached.expires_at - _REFRESH_SKEW > time.time():
            return cached.token

        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self._app_jwt()}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        url = f"{_API}/app/installations/{self.installation_id}/access_tokens"
        try:
            resp = httpx.post(url, headers=headers, timeout=30)
        except httpx.HTTPError as exc:  # network-level; message carries no secret
            raise GitHubError(f"installation token request failed: {type(exc).__name__}")
        if resp.status_code != 201:
            raise GitHubError(f"installation token denied (HTTP {resp.status_code})")
        data = resp.json()
        token = data["token"]
        expires = _parse_gh_time(data.get("expires_at"))
        _TOKEN_CACHE[self.installation_id] = _CachedToken(token=token, expires_at=expires)
        return token

    def token_scopes(self) -> dict:
        """Permissions of the current installation token (no secret returned)."""
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self._app_jwt()}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        url = f"{_API}/app/installations/{self.installation_id}/access_tokens"
        resp = httpx.post(url, headers=headers, timeout=30)
        if resp.status_code != 201:
            raise GitHubError(f"installation token denied (HTTP {resp.status_code})")
        return resp.json().get("permissions", {})

    # -- low-level request -------------------------------------------------

    def _request(self, method: str, path: str, *, json: dict | None = None) -> httpx.Response:
        """Authenticated REST call. ``path`` is API-absolute (starts with '/')."""
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"token {self._installation_token()}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        try:
            resp = httpx.request(method, f"{_API}{path}", headers=headers, json=json, timeout=60)
        except httpx.HTTPError as exc:
            raise GitHubError(f"{method} {path} failed: {type(exc).__name__}")
        return resp

    @staticmethod
    def _ok(resp: httpx.Response, *expected: int) -> dict:
        if resp.status_code not in expected:
            # GitHub error bodies do not contain our credentials; still, keep it short.
            raise GitHubError(f"GitHub API {resp.request.method} {resp.url.path} "
                              f"→ HTTP {resp.status_code}: {resp.text[:200]}")
        return resp.json() if resp.content else {}

    def verify_access(self) -> dict:
        """Confirm the App can see the repository (used by live certification)."""
        data = self._ok(self._request("GET", f"/repos/{self.repo}"), 200)
        return {
            "repo": data.get("full_name"),
            "default_branch": data.get("default_branch"),
            "private": data.get("private"),
            "permissions": data.get("permissions", {}),
        }

    def list_pulls(
        self, *, state: str = "closed", base: str | None = None,
        per_page: int = 50, max_pages: int = 5,
    ) -> list[dict]:
        """READ-ONLY: list Pull Requests (App token, ``pull_requests:read``).

        Used by the merge detector to reconcile which bridge PRs GitHub has
        merged. Never modifies anything — no new credential; the installation
        token's read scope is sufficient. Returns [] if the App is not configured.
        Each item carries ``number``, ``head.ref``, ``merged_at`` (None unless
        merged), and ``base.ref`` — enough to identify a merged bridge PR.
        """
        if not self.configured():
            return []
        out: list[dict] = []
        page = 1
        while page <= max_pages:
            q = f"state={state}&per_page={per_page}&page={page}&sort=updated&direction=desc"
            if base:
                q += f"&base={base}"
            data = self._ok(self._request("GET", f"/repos/{self.repo}/pulls?{q}"), 200)
            batch = data if isinstance(data, list) else []
            out.extend(batch)
            if len(batch) < per_page:
                break
            page += 1
        return out

    def list_installation_repositories(self) -> list[dict]:
        """READ-ONLY discovery: every repository the GitHub App installation can see.

        Used by Project ATLAS to discover connected repositories as business
        assets. Never modifies anything. Returns [] if the App is not configured.
        """
        if not self.configured():
            return []
        out: list[dict] = []
        page = 1
        while page <= 10:  # safety bound
            data = self._ok(
                self._request("GET", f"/installation/repositories?per_page=100&page={page}"), 200)
            repos = data.get("repositories", []) or []
            for r in repos:
                out.append({
                    "full_name": r.get("full_name"),
                    "name": r.get("name"),
                    "description": r.get("description"),
                    "default_branch": r.get("default_branch"),
                    "private": r.get("private"),
                    "language": r.get("language"),
                    "created_at": r.get("created_at"),
                    "pushed_at": r.get("pushed_at"),
                })
            if len(repos) < 100:
                break
            page += 1
        return out

    # -- pull requests -----------------------------------------------------

    def create_pull_request(
        self, *, head: str, base: str, title: str, body: str = "", draft: bool = False,
    ) -> dict:
        payload = {"title": title, "head": head, "base": base, "body": body, "draft": draft}
        data = self._ok(self._request("POST", f"/repos/{self.repo}/pulls", json=payload), 201)
        return _pr_view(data)

    def get_pull_request(self, number: int) -> dict:
        data = self._ok(self._request("GET", f"/repos/{self.repo}/pulls/{number}"), 200)
        return _pr_view(data)

    def update_pull_request(self, number: int, **fields) -> dict:
        allowed = {k: v for k, v in fields.items()
                   if k in ("title", "body", "state", "base")}
        data = self._ok(
            self._request("PATCH", f"/repos/{self.repo}/pulls/{number}", json=allowed), 200
        )
        return _pr_view(data)

    def request_reviewers(self, number: int, reviewers: list[str]) -> dict:
        """Assign human/team reviewers to a PR."""
        payload = {"reviewers": reviewers}
        data = self._ok(
            self._request(
                "POST", f"/repos/{self.repo}/pulls/{number}/requested_reviewers", json=payload
            ),
            201, 200,
        )
        return {"number": number, "requested_reviewers":
                [r.get("login") for r in data.get("requested_reviewers", [])]}

    def merge_pull_request(
        self, number: int, *, approved_by: str, method: str = "squash",
        commit_title: str | None = None,
    ) -> dict:
        """Merge a PR. Requires an explicit Founder approver (Blueprint Vol 05).

        The caller must pass ``approved_by`` — the human/authority that approved
        the merge. An empty approver is refused, so merge is never automatic.
        """
        if not approved_by or not str(approved_by).strip():
            raise GitHubError("merge refused: Founder approval is required (Blueprint Vol 05)")
        if method not in ("merge", "squash", "rebase"):
            raise GitHubError(f"invalid merge method: {method}")
        payload = {"merge_method": method}
        if commit_title:
            payload["commit_title"] = commit_title
        resp = self._request("PUT", f"/repos/{self.repo}/pulls/{number}/merge", json=payload)
        data = self._ok(resp, 200)
        return {"merged": bool(data.get("merged")), "sha": data.get("sha"),
                "number": number, "approved_by": approved_by}

    # -- repository management ---------------------------------------------

    def create_repository(
        self, name: str, *, private: bool = True, description: str = "",
        auto_init: bool = True, org: str | None = None,
    ) -> dict:
        """Create a repository under the installation account (or an org)."""
        payload = {"name": name, "private": private, "description": description,
                   "auto_init": auto_init}
        # A GitHub App installation token can create repositories only inside an
        # ORGANISATION it is installed on. It CANNOT create repositories under a
        # personal (user) account — GitHub returns 403 "Resource not accessible by
        # integration" regardless of the 'administration' permission. Detect the
        # target account type and fail with an accurate, actionable message.
        target_org = org
        if not target_org:
            owner = (self.repo.split("/")[0] if self.repo else "")
            if owner:
                acct = self._request("GET", f"/users/{owner}")
                if acct.status_code == 200 and acct.json().get("type") == "Organization":
                    target_org = owner
        if not target_org:
            raise GitHubError(
                "repository creation unavailable: the GitHub App is installed on a "
                "personal (user) account, and GitHub does not permit Apps to create "
                "repositories under a user account. Install the App on a GitHub "
                "Organization to enable repository creation/bootstrap."
            )
        resp = self._request("POST", f"/orgs/{target_org}/repos", json=payload)
        if resp.status_code == 403:
            raise GitHubError(
                "repository creation denied: the GitHub App lacks 'administration: "
                "write' on the organization (grant it in the App settings)"
            )
        data = self._ok(resp, 201)
        return {"full_name": data.get("full_name"), "default_branch": data.get("default_branch"),
                "ssh_url": data.get("ssh_url"), "clone_url": data.get("clone_url"),
                "private": data.get("private")}

    def configure_repository(self, repo: str | None = None, **settings) -> dict:
        """Update repository settings (e.g. delete_branch_on_merge, allow_squash_merge)."""
        target = repo or self.repo
        allowed = {k: v for k, v in settings.items() if k in (
            "description", "homepage", "private", "has_issues", "has_wiki",
            "allow_squash_merge", "allow_merge_commit", "allow_rebase_merge",
            "delete_branch_on_merge", "default_branch",
        )}
        data = self._ok(self._request("PATCH", f"/repos/{target}", json=allowed), 200)
        return {"full_name": data.get("full_name"),
                "delete_branch_on_merge": data.get("delete_branch_on_merge"),
                "allow_squash_merge": data.get("allow_squash_merge")}

    def branch_protection(self, branch: str | None = None, repo: str | None = None) -> dict:
        """Read the protection status of a branch (verification, read-only)."""
        target = repo or self.repo
        br = branch or get_settings().github_default_branch
        resp = self._request("GET", f"/repos/{target}/branches/{br}/protection")
        if resp.status_code == 404:
            return {"branch": br, "protected": False}
        if resp.status_code == 403:
            # The App installation lacks the 'administration: read' permission
            # required to read branch protection. Report honestly, don't crash.
            return {"branch": br, "protected": None,
                    "reason": "app lacks 'administration' permission to read protection"}
        data = self._ok(resp, 200)
        return {
            "branch": br,
            "protected": True,
            "required_reviews": bool(data.get("required_pull_request_reviews")),
            "required_status_checks": bool(data.get("required_status_checks")),
            "enforce_admins": (data.get("enforce_admins") or {}).get("enabled", False),
        }

    def repository_bootstrap(
        self, name: str, *, private: bool = True, description: str = "", org: str | None = None,
    ) -> dict:
        """Create + baseline-configure a repository, ready for WES delivery.

        Idempotent-ish: if the repo already exists the existing one is returned.
        Returns the transport URLs so ``GitService`` can push into it.
        """
        # If it already exists, reuse it rather than failing the bootstrap.
        owner = org or self.repo.split("/")[0] if self.repo else org
        full = f"{owner}/{name}" if owner else name
        existing = self._request("GET", f"/repos/{full}")
        if existing.status_code == 200:
            info = existing.json()
            created = False
        else:
            info = self.create_repository(
                name, private=private, description=description, auto_init=True, org=org
            )
            created = True
        # Baseline configuration per Blueprint Vol 04 (squash + branch cleanup).
        try:
            self.configure_repository(
                repo=info.get("full_name") or full,
                allow_squash_merge=True, delete_branch_on_merge=True,
            )
        except GitHubError:
            pass
        return {
            "created": created,
            "full_name": info.get("full_name") or full,
            "ssh_url": info.get("ssh_url"),
            "clone_url": info.get("clone_url"),
            "default_branch": info.get("default_branch", get_settings().github_default_branch),
        }


# -- helpers ---------------------------------------------------------------

def _pr_view(data: dict) -> dict:
    """Public projection of a PR (no tokens, no internal noise)."""
    return {
        "number": data.get("number"),
        "state": data.get("state"),
        "title": data.get("title"),
        "html_url": data.get("html_url"),
        "head": (data.get("head") or {}).get("ref"),
        "base": (data.get("base") or {}).get("ref"),
        "merged": data.get("merged", False),
        "mergeable": data.get("mergeable"),
        "draft": data.get("draft", False),
    }


def _parse_gh_time(value: str | None) -> float:
    """Parse GitHub's ISO-8601 'expires_at' into epoch seconds.

    Falls back to 'now + 55 min' when the field is missing, which is still safe
    because the refresh skew forces renewal well before a real token would lapse.
    """
    if not value:
        return time.time() + 55 * 60
    from datetime import datetime

    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.timestamp()
    except ValueError:
        return time.time() + 55 * 60

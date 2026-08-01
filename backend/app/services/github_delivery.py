"""GitHubDeliveryService — automatic push → PR → reviewer → merge (P0 final).

Wires the completed engineering result onto GitHub with NO manual developer
action, per Blueprint Vol 04 (PR → review → merge) and Vol 06 (GitHub is the
source of truth). It reuses:

* ``GitService``     — real git transport (branch/commit/push over the App token).
* ``GitHubService``  — the App-authenticated REST client (PR create/merge).

Every step is gated on ``GitHubService.configured()``. When GitHub is not
configured (the offline test suite, or a deployment without the App), delivery is
a no-op that returns ``delivered=False`` — so existing behaviour and all 423
tests are unchanged.

Merge is NEVER automatic: it happens only when the Founder approves, and only
through ``merge_on_approval`` with a real approver (Blueprint Vol 05 human-approval
model for irreversible actions).
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.domain.development_enums import DevTaskStatus, PRStatus
from app.models.development import DevelopmentTask, PullRequest


class GitHubDeliveryService:
    def __init__(self, db: Session):
        self.db = db

    # -- target resolution -------------------------------------------------

    def _target_repo(self, task: DevelopmentTask) -> str | None:
        """Repository this task delivers into.

        Preference: the project's registered repository; otherwise the
        studio-configured repo. Returns None when nothing is configured.
        """
        # A project-linked repository wins (each product owns its repo).
        try:
            from app.models.repository import Repository

            if task.repository_id:
                repo = self.db.get(Repository, task.repository_id)
                # Repository.slug stores "owner/name" when GitHub-backed.
                if repo and repo.slug and "/" in repo.slug:
                    return repo.slug
        except Exception:
            pass
        return get_settings().github_repo or None

    def _base_branch(self, task: DevelopmentTask) -> str:
        s = get_settings()
        return s.github_delivery_base or s.github_default_branch or "main"

    # -- delivery (push + PR + reviewer) -----------------------------------

    def deliver(self, task: DevelopmentTask, git, *, base: str | None = None) -> dict:
        """Push the task branch and open a real GitHub PR. Idempotent per task.

        Returns a structured record; ``delivered=False`` (with a reason) whenever
        GitHub is not configured or there is nothing to deliver — never raises for
        those expected conditions, so the surrounding workflow is unaffected.
        """
        from app.services.github_service import GitHubService

        if not GitHubService.configured():
            return {"delivered": False, "reason": "github app not configured"}
        repo = self._target_repo(task)
        if not repo:
            return {"delivered": False, "reason": "no target repository configured"}
        base = base or self._base_branch(task)
        branch = task.branch_name or (git.current_branch() if git else None)
        if not branch:
            return {"delivered": False, "reason": "task has no branch"}

        gh = GitHubService(repo=repo)
        token = gh._installation_token()

        # 1. push the feature branch (App token, never main).
        push = git.push_via_app(token, repo, branch)

        # 2. open the PR (reuse the local draft's title/body when present).
        pr_row = self.db.scalar(select(PullRequest).where(PullRequest.task_id == task.id))
        title = (pr_row.title if pr_row else None) or f"{task.code}: {task.title}"
        body = (pr_row.body if pr_row else None) or f"Autonomous delivery for {task.code}."
        pr = gh.create_pull_request(head=branch, base=base, title=title[:300], body=body)

        # 3. assign a reviewer when one is configured (best-effort).
        reviewer = get_settings().github_repo.split("/")[0] if get_settings().github_repo else None
        reviewers: list[str] = []
        if reviewer:
            try:
                res = gh.request_reviewers(pr["number"], [reviewer])
                reviewers = res.get("requested_reviewers", [])
            except Exception:
                reviewers = []

        # 4. persist the real PR onto the row (create the row if the draft is absent).
        if pr_row is None:
            pr_row = PullRequest(task_id=task.id, branch_name=branch, base_branch=base,
                                 title=title[:300], body=body)
            self.db.add(pr_row)
        pr_row.github_repo = repo
        pr_row.github_number = pr["number"]
        pr_row.github_url = pr["html_url"]
        pr_row.base_branch = base
        pr_row.status = PRStatus.OPEN
        self.db.flush()

        return {
            "delivered": True,
            "repo": repo,
            "branch": branch,
            "base": base,
            "pr_number": pr["number"],
            "pr_url": pr["html_url"],
            "head_sha": push.get("head_sha"),
            "reviewers": reviewers,
        }

    # -- merge on Founder approval -----------------------------------------

    def merge_on_approval(self, task_id: uuid.UUID, *, approved_by: str,
                          method: str = "squash") -> dict:
        """Merge the task's GitHub PR after Founder approval. No approver → refused.

        Called from the approval path; a no-op (``merged=False``) when there is no
        real GitHub PR (e.g. offline), so approval of a local-only task still works.
        """
        from app.services.github_service import GitHubService

        # Prefer the delivered PR (one with a real github_number); a task may carry
        # several draft rows from re-runs, only one of which was pushed to GitHub.
        pr_row = self.db.scalar(
            select(PullRequest)
            .where(PullRequest.task_id == task_id, PullRequest.github_number.isnot(None))
            .order_by(PullRequest.created_at.desc())
        )
        if not pr_row or not pr_row.github_number or not pr_row.github_repo:
            return {"merged": False, "reason": "no github pull request for this task"}
        if not GitHubService.configured():
            return {"merged": False, "reason": "github app not configured"}

        gh = GitHubService(repo=pr_row.github_repo)
        result = gh.merge_pull_request(
            pr_row.github_number, approved_by=approved_by, method=method,
            commit_title=f"{pr_row.title}"[:100],
        )
        if result.get("merged"):
            from datetime import datetime, timezone

            pr_row.status = PRStatus.MERGED
            pr_row.merged_sha = result.get("sha")
            pr_row.merged_at = datetime.now(timezone.utc)
            task = self.db.get(DevelopmentTask, task_id)
            if task:
                task.status = DevTaskStatus.MERGED
            self.db.flush()
        return result

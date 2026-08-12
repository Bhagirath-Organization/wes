"""B6 merge detection — auto-advance a bridge-opened PR's lifecycle on merge.

The F10 bridge opens a PR and stops; the Founder merges it (PROMPT-SYS §6). This
module closes the last stitch of full autonomy: it *detects* that a
bridge-opened PR has been merged and fires :func:`advance_on_merge` so the
development task, its work item, and its project advance to reality — without a
human having to tell the system "it merged".

Design (the five properties this must have):

1. **Mechanism = poll, not event.** Each pass calls the GitHub REST API (App
   token, read scope) for closed PRs and reconciles GitHub's *merged* state
   against the DB. It is deliberately a **reconciliation**, not an event
   subscription: there is no webhook to miss. **Catch-up** is therefore free — a
   PR merged while the detector (or the whole app) was down is simply seen on the
   next pass, because the pass reads the current merged state, not a delta.
   Cadence: ``bridge_merge_detection_interval_s`` (default 300 s).

2. **Idempotent firing.** A task already at ``MERGED`` is skipped (``already``);
   and :func:`advance_on_merge` is itself a no-op on an already-merged task. So
   detecting the same merge twice advances nothing the second time.

3. **Scope = bridge PRs only.** Only PRs whose head branch starts with
   ``feature/bridge/`` are ever mapped to a task. A merged governed PR
   (``fix/*``, ``docs/*``, …) is counted and ignored — it can *never* trigger an
   auto-advancement, even if a same-named task exists.

4. **Identity = the App token's read scope.** The read reuses
   :class:`GitHubService` (the same installation token the bridge already uses);
   ``pull_requests:read`` is sufficient. No new credential is introduced.

5. **Postgres-parity (F15).** The detector writes **no new value-shape** to any
   column — it only transitions existing enum columns already exercised on
   Postgres (``DevTaskStatus``/``WorkStatus``/``ProjectStatus``). There is no new
   varchar/width surface, so the F15 parity check is N/A by construction.
"""

from __future__ import annotations

import logging
import threading

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.domain.development_enums import DevTaskStatus
from app.models.development import DevelopmentTask
from app.services.bridge import BRANCH_PREFIX  # "feature/bridge/"
from app.services.bridge_lifecycle import advance_on_merge

logger = logging.getLogger("wes.merge_detection")


def _status_value(s) -> str:
    return s.value if hasattr(s, "value") else s


def detect_and_advance_bridge_merges(
    db: Session, gh, *, commit: bool = True, prefix: str = BRANCH_PREFIX,
) -> dict:
    """One reconciliation pass: advance the dev-task of every merged bridge PR.

    ``gh`` is any object exposing ``list_pulls(state=, base=)`` — the real
    :class:`GitHubService` in production; a fake in tests. Returns a summary:
    ``advanced`` (task codes moved to merged this pass), ``already`` (were merged),
    ``no_task`` (merged bridge branch with no matching task), ``non_bridge`` (count
    of merged PRs skipped for scope), ``scanned`` (merged PRs examined).
    """
    summary = {
        "scanned": 0, "advanced": [], "already": [], "no_task": [], "non_bridge": 0,
    }
    pulls = gh.list_pulls(state="closed", base=get_settings().github_default_branch)
    for pr in pulls or []:
        if not pr.get("merged_at"):
            continue  # closed-but-not-merged never advances anything
        summary["scanned"] += 1
        head_ref = ((pr.get("head") or {}).get("ref")) or ""
        # POINT 3 — scope: only bridge branches may ever fire.
        if not head_ref.startswith(prefix):
            summary["non_bridge"] += 1
            continue
        code = head_ref[len(prefix):]
        dev = db.scalar(
            select(DevelopmentTask).where(func.lower(DevelopmentTask.code) == code.lower())
        )
        if dev is None:
            summary["no_task"].append(head_ref)
            continue
        # POINT 2 — idempotency: an already-merged task is a no-op.
        if _status_value(dev.status) == DevTaskStatus.MERGED.value:
            summary["already"].append(dev.code)
            continue
        advance_on_merge(db, dev, commit=False)  # itself idempotent
        summary["advanced"].append(dev.code)
        logger.info("B6: advanced %s on merge of PR #%s (%s)",
                    dev.code, pr.get("number"), head_ref)
    if commit and summary["advanced"]:
        db.commit()
    return summary


class BridgeMergeDetector:
    """A thin, dedicated poller that runs :func:`detect_and_advance_bridge_merges`
    on an interval. Mirrors ``JobWorker``: ``run_once`` is deterministic and
    directly tested; ``start`` spawns a daemon thread that loops. One detector =
    one chain, so there is no duplicate-pass pile-up across restarts.
    """

    def __init__(self, session_factory, *, gh=None, interval_s: int | None = None):
        self.session_factory = session_factory
        self._gh = gh  # injectable; defaults to a real GitHubService per pass
        self.interval_s = (
            interval_s if interval_s is not None
            else get_settings().bridge_merge_detection_interval_s
        )
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def _client(self):
        if self._gh is not None:
            return self._gh
        # POINT 4 — identity: reuse the App installation token (read scope). No
        # new credential; a fresh service per pass so the token stays current.
        from app.services.github_service import GitHubService

        return GitHubService()

    def run_once(self) -> dict:
        """One reconciliation pass in its own session. Never raises to the loop."""
        db = self.session_factory()
        try:
            return detect_and_advance_bridge_merges(db, self._client(), commit=True)
        finally:
            db.close()

    def start(self) -> None:
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="wes-bridge-merge-detector"
        )
        self._thread.start()

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self.run_once()
            except Exception:  # noqa: BLE001 - a poll failure must not kill the loop
                logger.exception("bridge merge detection pass failed; will retry")
            finally:
                self._stop.wait(self.interval_s)

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)

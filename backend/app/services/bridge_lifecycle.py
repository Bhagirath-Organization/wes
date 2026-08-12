"""F10-PR-2 — lifecycle truth (design §B step B6).

Two things live here:

* :func:`advance_on_merge` — the reusable B6 mechanism the bridge calls when a
  bridge-opened PR is merged: the development task advances to ``merged``, its
  linked work item to ``done``, and the project past ``planning`` (to
  ``completed`` once every work item is done, else ``active``). PR-3 wires this
  to real merge detection; PR-2 delivers and tests the mechanism.

* :func:`reconcile_test_mission_01` — the one-time, **idempotent**, **honest**
  reconciliation of the five TEST-MISSION-01 development-task mirrors that have
  sat ``pr_ready`` since 2026-08-07 (the reason the mission card reads "Review /
  70%" for a Founder-accepted, shipped mission). It does NOT green-wash: only
  T001/T002/T003 (the ``truncate()`` spec/impl/tests) actually shipped — via the
  human-governed PR #13 — so only they become ``merged`` + ``done``. T004's docs
  were **returned** in the mission review (``changes_requested``); T005 was a
  Phase-2 follow-up ticket the mission filed (``completed``). Keyed on the stable
  ``work_items.task_code`` (not the seed-order DEV-#### code), it runs at deploy
  time through the seed path and no-ops once the rows are in their target state.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.development_enums import DevTaskStatus
from app.domain.work_enums import ProjectStatus, WorkStatus
from app.models.development import DevelopmentTask
from app.models.work import Project, WorkItem

# The honest per-mirror mapping (work_item task_code -> (dev_task status, work status)).
# T001/T002/T003 shipped in PR #13; T004 was returned; T005 filed a follow-up ticket.
_TEST_MISSION_01_RECONCILE: dict[str, tuple[DevTaskStatus, WorkStatus]] = {
    "TEST-MISSION-01-T001": (DevTaskStatus.MERGED, WorkStatus.DONE),
    "TEST-MISSION-01-T002": (DevTaskStatus.MERGED, WorkStatus.DONE),
    "TEST-MISSION-01-T003": (DevTaskStatus.MERGED, WorkStatus.DONE),
    "TEST-MISSION-01-T004": (DevTaskStatus.CHANGES_REQUESTED, WorkStatus.REVIEW),
    "TEST-MISSION-01-T005": (DevTaskStatus.COMPLETED, WorkStatus.DONE),
}


def _advance_project(db: Session, project_id: uuid.UUID) -> None:
    """Move a project past ``planning`` based on its work items' truth."""
    project = db.get(Project, project_id)
    if project is None:
        return
    items = list(db.scalars(select(WorkItem).where(WorkItem.project_id == project_id)).all())
    if not items:
        return
    done = all(_status_value(w.status) == WorkStatus.DONE.value for w in items)
    if done:
        project.status = ProjectStatus.COMPLETED
    elif _status_value(project.status) == ProjectStatus.PLANNING.value:
        project.status = ProjectStatus.ACTIVE
    db.flush()


def _status_value(s) -> str:
    return s.value if hasattr(s, "value") else s


def advance_on_merge(db: Session, dev_task: DevelopmentTask, *, commit: bool = False) -> None:
    """B6: a bridge-opened PR merged — advance the task, its work item, the project.

    Idempotent: re-running on an already-merged task is a no-op.
    """
    dev_task.status = DevTaskStatus.MERGED
    if dev_task.work_item_id is not None:
        wi = db.get(WorkItem, dev_task.work_item_id)
        if wi is not None:
            wi.status = WorkStatus.DONE
            db.flush()
            _advance_project(db, wi.project_id)
    db.flush()
    if commit:
        db.commit()


def reconcile_test_mission_01(db: Session, *, commit: bool = True) -> int:
    """One-time idempotent reconciliation of the 5 TEST-MISSION-01 mirrors.

    Returns the number of rows written (0 once already reconciled). Honest by
    construction — see the module docstring for why T004/T005 do not become
    ``merged``.
    """
    changed = 0
    for task_code, (dev_status, work_status) in _TEST_MISSION_01_RECONCILE.items():
        wi = db.scalar(select(WorkItem).where(WorkItem.task_code == task_code))
        if wi is None:
            continue
        if _status_value(wi.status) != work_status.value:
            wi.status = work_status
            changed += 1
        dev = db.scalar(select(DevelopmentTask).where(DevelopmentTask.work_item_id == wi.id))
        if dev is not None and _status_value(dev.status) != dev_status.value:
            dev.status = dev_status
            changed += 1
    if changed:
        db.flush()
        # Advance the mission project on the reconciled truth.
        wi = db.scalar(
            select(WorkItem).where(WorkItem.task_code == "TEST-MISSION-01-T001")
        )
        if wi is not None:
            _advance_project(db, wi.project_id)
        if commit:
            db.commit()
    return changed

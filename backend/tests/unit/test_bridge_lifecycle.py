"""F10-PR-2 tests — lifecycle truth (B6 advancement, review trigger, reconciliation).

The reconciliation is proven HONEST, not just green: T004 (returned) never
becomes ``merged``.
"""

from __future__ import annotations

import pytest

from app.domain.development_enums import DevTaskStatus
from app.domain.orchestration_enums import ReviewOutcome
from app.domain.work_enums import ProjectStatus, WorkStatus
from app.models.development import DevelopmentTask
from app.models.work import Project, WorkItem
from app.services.bridge_lifecycle import advance_on_merge, reconcile_test_mission_01


def _project(db, code="P-1", status=ProjectStatus.PLANNING):
    p = Project(code=code, name=code, status=status)
    db.add(p)
    db.flush()
    return p


def _item(db, project, code, status=WorkStatus.IN_PROGRESS):
    w = WorkItem(project_id=project.id, task_code=code, title=code, status=status)
    db.add(w)
    db.flush()
    return w


def _dev(db, wi, code, status=DevTaskStatus.PR_READY):
    d = DevelopmentTask(code=code, title=code, status=status, work_item_id=wi.id)
    db.add(d)
    db.flush()
    return d


# --- B6 advance_on_merge ----------------------------------------------------


def test_advance_on_merge_moves_task_item_project(db_session):
    p = _project(db_session)
    wi = _item(db_session, p, "P1-T1")
    dev = _dev(db_session, wi, "DEV-A")
    advance_on_merge(db_session, dev)
    assert dev.status == DevTaskStatus.MERGED
    assert wi.status == WorkStatus.DONE
    # single item, now done -> project completed
    assert db_session.get(Project, p.id).status == ProjectStatus.COMPLETED


def test_project_only_completes_when_all_items_done(db_session):
    p = _project(db_session)
    w1 = _item(db_session, p, "P1-A")
    _item(db_session, p, "P1-B")  # stays in_progress
    dev = _dev(db_session, w1, "DEV-B")
    advance_on_merge(db_session, dev)
    # one of two done -> project active (past planning), not completed
    assert db_session.get(Project, p.id).status == ProjectStatus.ACTIVE


def test_advance_on_merge_idempotent(db_session):
    p = _project(db_session)
    wi = _item(db_session, p, "P1-T")
    dev = _dev(db_session, wi, "DEV-C")
    advance_on_merge(db_session, dev)
    advance_on_merge(db_session, dev)  # no error, still merged/done
    assert dev.status == DevTaskStatus.MERGED and wi.status == WorkStatus.DONE


# --- review-verdict trigger -------------------------------------------------


@pytest.mark.usefixtures("orch_seeded")
def test_approved_verdict_advances_work_item_to_review(db_session):
    from app.models.ai import AIEmployee
    from app.services.orchestration import OrchestrationService
    from app.services.providers_service import ProviderService

    svc = OrchestrationService(db_session)
    emp = db_session.query(AIEmployee).filter_by(employee_code="AI-EMP-005").one()
    wi = db_session.query(WorkItem).first()
    wi.status = WorkStatus.IN_PROGRESS
    db_session.flush()
    mock = ProviderService(db_session).get_by_name("mock")
    run = svc.run_stage(emp.id, wi.id, provider_name="mock")
    import uuid as _uuid

    svc.review_run(_uuid.UUID(run["id"]), ReviewOutcome.APPROVED)
    assert db_session.get(WorkItem, wi.id).status == WorkStatus.REVIEW
    assert mock is not None


@pytest.mark.usefixtures("orch_seeded")
def test_returned_verdict_does_not_advance(db_session):
    from app.models.ai import AIEmployee
    from app.services.orchestration import OrchestrationService

    svc = OrchestrationService(db_session)
    emp = db_session.query(AIEmployee).filter_by(employee_code="AI-EMP-005").one()
    wi = db_session.query(WorkItem).first()
    wi.status = WorkStatus.IN_PROGRESS
    db_session.flush()
    run = svc.run_stage(emp.id, wi.id, provider_name="mock")
    import uuid as _uuid

    svc.review_run(_uuid.UUID(run["id"]), ReviewOutcome.RETURNED)
    assert db_session.get(WorkItem, wi.id).status == WorkStatus.IN_PROGRESS  # unchanged


# --- one-time reconciliation (HONEST) --------------------------------------


def _mission_fixture(db):
    p = _project(db, code="TEST-MISSION-01")
    mapping = {
        "TEST-MISSION-01-T001": "DEV-0131",
        "TEST-MISSION-01-T002": "DEV-0132",
        "TEST-MISSION-01-T003": "DEV-0133",
        "TEST-MISSION-01-T004": "DEV-0134",
        "TEST-MISSION-01-T005": "DEV-0135",
    }
    for wc, dc in mapping.items():
        wi = _item(db, p, wc)
        _dev(db, wi, dc)
    return p


def test_reconciliation_is_honest_t004_not_merged(db_session):
    p = _mission_fixture(db_session)
    n = reconcile_test_mission_01(db_session, commit=False)
    assert n > 0

    def dev_status(code):
        return db_session.query(DevelopmentTask).filter_by(code=code).one().status

    def wi_status(code):
        return db_session.query(WorkItem).filter_by(task_code=code).one().status

    # Shipped work (PR #13) -> merged / done.
    for c in ("DEV-0131", "DEV-0132", "DEV-0133"):
        assert dev_status(c) == DevTaskStatus.MERGED
    for c in ("TEST-MISSION-01-T001", "TEST-MISSION-01-T002", "TEST-MISSION-01-T003"):
        assert wi_status(c) == WorkStatus.DONE
    # T004 was RETURNED in the mission — must NOT be merged (honesty).
    assert dev_status("DEV-0134") == DevTaskStatus.CHANGES_REQUESTED
    assert dev_status("DEV-0134") != DevTaskStatus.MERGED
    assert wi_status("TEST-MISSION-01-T004") == WorkStatus.REVIEW
    # T005 filed the Phase-2 ticket -> completed / done.
    assert dev_status("DEV-0135") == DevTaskStatus.COMPLETED
    # Project advanced off planning (not completed — T004 not done).
    assert db_session.get(Project, p.id).status == ProjectStatus.ACTIVE


def test_reconciliation_idempotent(db_session):
    _mission_fixture(db_session)
    first = reconcile_test_mission_01(db_session, commit=False)
    second = reconcile_test_mission_01(db_session, commit=False)
    assert first > 0 and second == 0  # no-op once reconciled


def test_reconciliation_noop_without_mission(db_session):
    assert reconcile_test_mission_01(db_session, commit=False) == 0

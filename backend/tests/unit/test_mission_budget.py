"""Mission Budget Envelope tests (WES-DEC-011 implementation).

Pins the envelope's full lifecycle: itemised intake estimate; the single
approval creating a ``mission:<id>``-scoped ``BudgetConfig``; spend attribution
via ``provider_usage.project_id`` (including the reasoning path through
``mission_context``); the 80% notify-once and 100% hard-stop + escalation
triggers inside ``run_stage``; and the retirement of the global per-run cap for
envelope-covered runs.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.models.provider_platform import BudgetConfig, ProviderEvent, ProviderUsage
from app.services.mission_budget import (
    GOVERNED_CALL_BASELINE_USD,
    REASONING_OVERHEAD_USD,
    MissionBudgetService,
    current_project_id,
    mission_context,
)


def _usage(db, project_id, cost):
    from app.models.orchestration import AIProvider

    provider = db.query(AIProvider).first()
    now = datetime.now(timezone.utc)
    db.add(
        ProviderUsage(
            provider_id=provider.id,
            project_id=project_id,
            estimated_cost=cost,
            actual_cost=cost,
            day=now.strftime("%Y-%m-%d"),
            month=now.strftime("%Y-%m"),
        )
    )
    db.flush()


def test_estimate_math_is_itemised():
    est = MissionBudgetService.__new__(MissionBudgetService).estimate(5)
    assert est["execution_estimate"] == round(5 * GOVERNED_CALL_BASELINE_USD, 2)
    assert est["reasoning_overhead"] == REASONING_OVERHEAD_USD
    expected = round((5 * GOVERNED_CALL_BASELINE_USD + REASONING_OVERHEAD_USD) * 1.25, 2)
    assert est["estimated_total"] == expected
    assert "approve?" in est["ask"] and f"${expected:.2f}" in est["ask"]


@pytest.mark.usefixtures("orch_seeded")
def test_approve_creates_scoped_envelope(db_session):
    pid = uuid.uuid4()
    svc = MissionBudgetService(db_session)
    env = svc.approve(pid, 3.50)
    assert env.scope == f"mission:{pid}"
    assert env.max_cost == 3.50 and env.hard_stop and env.warning_threshold == 0.8
    # Idempotent update, not duplicate rows.
    svc.approve(pid, 5.00)
    rows = db_session.query(BudgetConfig).filter_by(scope=f"mission:{pid}").all()
    assert len(rows) == 1 and rows[0].max_cost == 5.00
    with pytest.raises(ValueError):
        svc.approve(pid, 0)


@pytest.mark.usefixtures("orch_seeded")
def test_check_thresholds(db_session):
    pid = uuid.uuid4()
    svc = MissionBudgetService(db_session)
    assert svc.check(pid)["covered"] is False  # no envelope -> not covered
    svc.approve(pid, 1.00)
    assert svc.check(pid, 0.10)["status"] == "ok"
    _usage(db_session, pid, 0.75)
    assert svc.check(pid, 0.10)["status"] == "warn80"  # 0.85 projected
    _usage(db_session, pid, 0.30)
    assert svc.check(pid, 0.0)["status"] == "exceeded"  # 1.05 spent


@pytest.mark.usefixtures("orch_seeded")
def test_reasoning_path_attributed_via_mission_context(db_session):
    from app.models.orchestration import AIProvider
    from app.providers import ExecutionRequest, Message
    from app.services.provider_orchestrator import AIProviderOrchestrator

    row = db_session.query(AIProvider).filter_by(name="mock").one()
    row.enabled = True
    db_session.flush()
    pid = uuid.uuid4()
    assert current_project_id() is None
    with mission_context(pid):
        assert current_project_id() == pid
        AIProviderOrchestrator(db_session).execute(
            ExecutionRequest(messages=[Message(role="user", content="attribute me")]),
            prefer="mock",
        )
    assert current_project_id() is None
    latest = (
        db_session.query(ProviderUsage).order_by(ProviderUsage.created_at.desc()).first()
    )
    rows = db_session.query(ProviderUsage).filter_by(project_id=pid).all()
    assert len(rows) == 1 and latest is not None


@pytest.mark.usefixtures("orch_seeded")
def test_run_stage_hard_stops_at_100_with_escalation(db_session):
    from app.models.ai import AIEmployee
    from app.models.work import WorkItem
    from app.services.orchestration import OrchestrationService

    ritchie = db_session.query(AIEmployee).filter_by(employee_code="AI-EMP-005").one()
    wi = db_session.query(WorkItem).first()
    svc_mb = MissionBudgetService(db_session)
    svc_mb.approve(wi.project_id, 0.50)
    _usage(db_session, wi.project_id, 0.60)  # already over
    run = OrchestrationService(db_session).run_stage(ritchie.id, wi.id, provider_name="mock")
    assert run["status"] == "failed"
    assert "envelope exhausted" in (run["error"] or "")
    ev = db_session.query(ProviderEvent).filter_by(event_type="envelope.exceeded").first()
    assert ev is not None


@pytest.mark.usefixtures("orch_seeded")
def test_run_stage_warns_once_at_80(db_session):
    from app.models.ai import AIEmployee
    from app.models.work import WorkItem
    from app.services.orchestration import OrchestrationService

    ritchie = db_session.query(AIEmployee).filter_by(employee_code="AI-EMP-005").one()
    wi = db_session.query(WorkItem).first()
    MissionBudgetService(db_session).approve(wi.project_id, 10.00)
    _usage(db_session, wi.project_id, 8.50)  # 85%
    svc = OrchestrationService(db_session)
    r1 = svc.run_stage(ritchie.id, wi.id, provider_name="mock")
    assert r1["status"] == "completed"  # free run inside the envelope
    r2 = svc.run_stage(ritchie.id, wi.id, provider_name="mock")
    warns = db_session.query(ProviderEvent).filter_by(event_type="envelope.warn80").all()
    assert len(warns) == 1  # notified exactly once
    assert r2["status"] in ("completed", "failed")  # second run not warn-blocked


@pytest.mark.usefixtures("orch_seeded")
def test_envelope_covered_run_ignores_global_per_run_cap(db_session):
    """WES-DEC-011: per-run max_cost is retired for covered runs."""
    from app.models.ai import AIEmployee
    from app.models.work import WorkItem
    from app.services.budget_service import BudgetService
    from app.services.orchestration import OrchestrationService

    ritchie = db_session.query(AIEmployee).filter_by(employee_code="AI-EMP-005").one()
    wi = db_session.query(WorkItem).first()
    # A global per-run cap that would block ANY call…
    BudgetService(db_session).update_config(max_cost=0.0000001, hard_stop=True)
    # …but the mission is envelope-covered with room to spare.
    MissionBudgetService(db_session).approve(wi.project_id, 10.00)
    run = OrchestrationService(db_session).run_stage(ritchie.id, wi.id, provider_name="mock")
    assert run["status"] == "completed"

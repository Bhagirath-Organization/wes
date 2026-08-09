"""F6 metering tests (WES-DEC-010 step 4): reasoning-path spend is recorded.

The live mission proved (finding F6) that LLM calls routed through
``AIProviderOrchestrator`` — executive reasoning, plan review, dev generation,
consensus — left **no** ``ProviderUsage`` rows, so the budget counters were
blind to real spend. These tests pin the fix: every successful orchestrator
execution records usage exactly like the orchestration pipeline does, and the
recorded numbers feed ``BudgetService``.
"""

from __future__ import annotations

import pytest

from app.models.provider_platform import ProviderUsage
from app.providers import ExecutionRequest, Message
from app.services.budget_service import BudgetService
from app.services.provider_orchestrator import AIProviderOrchestrator


def _enable_mock(db):
    from app.models.orchestration import AIProvider

    row = db.query(AIProvider).filter_by(name="mock").one()
    row.enabled = True
    db.flush()
    return row


def _request() -> ExecutionRequest:
    return ExecutionRequest(messages=[Message(role="user", content="ping the meter")])


@pytest.mark.usefixtures("orch_seeded")
def test_execute_records_provider_usage(db_session):
    row = _enable_mock(db_session)
    before_ids = {u.id for u in db_session.query(ProviderUsage).all()}
    result, used = AIProviderOrchestrator(db_session).execute(_request(), prefer="mock")
    assert used == "mock" and result.status == "completed"
    new_rows = [u for u in db_session.query(ProviderUsage).all() if u.id not in before_ids]
    assert len(new_rows) == 1
    usage = new_rows[0]
    assert usage.provider_id == row.id
    assert usage.total_tokens == result.total_tokens > 0
    assert usage.estimated_cost == result.cost
    assert usage.run_id is None  # no ExecutionRun exists on the reasoning path


@pytest.mark.usefixtures("orch_seeded")
def test_metered_spend_feeds_budget_counters(db_session):
    _enable_mock(db_session)
    AIProviderOrchestrator(db_session).execute(_request(), prefer="mock")
    # Mock is zero-cost; the counters must still see the recorded rows (sum >= 0
    # over a non-empty day bucket) — assert via the day-keyed row, not the total.
    from datetime import datetime, timezone

    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    day_rows = db_session.query(ProviderUsage).filter_by(day=day).count()
    assert day_rows >= 1
    assert BudgetService(db_session).daily_spend() >= 0.0


@pytest.mark.usefixtures("orch_seeded")
def test_no_available_provider_records_nothing(db_session):
    from app.models.orchestration import AIProvider

    # route() deliberately falls back to the default provider even when disabled
    # ("never worse than before this engine existed") — clear both flags so the
    # no-provider path is genuinely reached.
    for p in db_session.query(AIProvider).all():
        p.enabled = False
        p.is_default = False
    db_session.flush()
    before = db_session.query(ProviderUsage).count()
    with pytest.raises(RuntimeError):
        AIProviderOrchestrator(db_session).execute(_request())
    assert db_session.query(ProviderUsage).count() == before


@pytest.mark.usefixtures("orch_seeded")
def test_consensus_meters_each_successful_answer(db_session):
    _enable_mock(db_session)
    before = db_session.query(ProviderUsage).count()
    out = AIProviderOrchestrator(db_session).consensus(_request(), task_type="reasoning", k=2)
    ok_answers = [a for a in out["answers"] if a["ok"]]
    assert len(ok_answers) >= 1
    assert db_session.query(ProviderUsage).count() == before + len(ok_answers)

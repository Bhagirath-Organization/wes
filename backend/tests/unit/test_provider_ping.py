"""Pre-flight PR-3: the budget-gated provider connectivity ping.

Uses the seeded ``mock`` provider (deterministic, zero-cost) so the money path is
exercised without a real API call. Covers: a successful ping records usage; a
hard-stop budget breach raises ``BudgetExceededError`` before the provider is
contacted (no usage recorded); and no configured provider is a clear error.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.core.exceptions import ValidationError
from app.models.provider_platform import BudgetConfig, ProviderUsage
from app.services.budget_service import BudgetExceededError
from app.services.provider_ping import ProviderPingService
from app.services.providers_service import ProviderService


def _mock_provider(db):
    return ProviderService(db).get_by_name("mock")


def _usage_count(db):
    return db.query(ProviderUsage).count()


def test_ping_records_usage_and_reports_spend(orch_seeded, db_session):
    provider = _mock_provider(db_session)
    before = _usage_count(db_session)

    result = ProviderPingService(db_session).ping(provider.id)

    assert result["ok"] is True
    assert result["provider"] == "mock"
    assert result["total_tokens"] >= 1
    assert "daily_spent" in result and "monthly_spent" in result
    # The ping's usage is recorded so it counts against the budget.
    assert _usage_count(db_session) == before + 1


def test_ping_blocked_by_hard_stop_raises_and_records_nothing(orch_seeded, db_session):
    provider = _mock_provider(db_session)
    now = datetime.now(timezone.utc)
    # Pre-spend above a hard daily limit so the projected spend is over budget.
    db_session.add(
        ProviderUsage(
            provider_id=provider.id,
            estimated_cost=10.0,
            actual_cost=10.0,
            day=now.strftime("%Y-%m-%d"),
            month=now.strftime("%Y-%m"),
        )
    )
    cfg = db_session.query(BudgetConfig).filter_by(scope="global").one_or_none()
    if cfg is None:
        cfg = BudgetConfig(scope="global")
        db_session.add(cfg)
    cfg.daily_cost_limit = 5.0
    cfg.hard_stop = True
    db_session.commit()

    before = _usage_count(db_session)
    with pytest.raises(BudgetExceededError):
        ProviderPingService(db_session).ping(provider.id)
    # Aborted before contacting the provider — no new usage recorded.
    assert _usage_count(db_session) == before


def test_ping_without_provider_raises_validation(db_session):
    with pytest.raises(ValidationError):
        ProviderPingService(db_session).ping()

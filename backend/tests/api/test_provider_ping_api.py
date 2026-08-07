"""Pre-flight PR-3: the budget-gated provider ping endpoint (Founder-only)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.domain.roles import Role
from app.models.provider_platform import BudgetConfig, ProviderUsage


def _mock_provider_id(client) -> str:
    providers = client.get("/api/v1/providers").json()["data"]
    return next(p["id"] for p in providers if p["name"] == "mock")


def test_ping_founder_ok(client, orch_seeded):
    pid = _mock_provider_id(client)
    resp = client.post(f"/api/v1/providers/{pid}/ping")
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["ok"] is True and data["provider"] == "mock"


def test_ping_forbidden_for_non_founder(client, as_role, orch_seeded):
    pid = _mock_provider_id(client)
    as_role(Role.DEPARTMENT_HEAD)
    assert client.post(f"/api/v1/providers/{pid}/ping").status_code == 403
    as_role(Role.EMPLOYEE)
    assert client.post(f"/api/v1/providers/{pid}/ping").status_code == 403


def test_ping_budget_hard_stop_returns_402(client, orch_seeded, db_session):
    pid = _mock_provider_id(client)
    now = datetime.now(timezone.utc)
    db_session.add(
        ProviderUsage(
            provider_id=uuid.UUID(pid),
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

    resp = client.post(f"/api/v1/providers/{pid}/ping")
    assert resp.status_code == 402, resp.text

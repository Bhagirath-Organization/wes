"""Provider connectivity ping, gated by the budget (pre-flight for the live mission).

Verifies that a configured provider answers a minimal request end-to-end while
proving the money path works: the budget is checked **before** the provider is
contacted and — per TEST-MISSION-CHARTER §8 — a hard-stop breach raises
``BudgetExceededError`` so the ping aborts without spending. On success the tiny
real usage is recorded (``CostEngine``) so it counts against the budget exactly
like any execution.

This is the same gate the orchestration pipeline applies, isolated into a
single, cheap, side-effect-light call the Founder can run to confirm the provider
and the $5 cap are wired before the mission.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError
from app.providers import ExecutionRequest, Message
from app.services.budget_service import BudgetExceededError, BudgetService
from app.services.provider_platform import CostEngine
from app.services.providers_service import ProviderService


class ProviderPingService:
    """A minimal, budget-gated provider connectivity check."""

    PING_PROMPT = "Reply with the single word: pong."
    PING_MAX_TOKENS = 16

    def __init__(self, db: Session, actor: str = "System"):
        self.db = db
        self.providers = ProviderService(db, actor=actor)
        self.budget = BudgetService(db)
        self.cost_engine = CostEngine(db)

    def ping(self, provider_id: uuid.UUID | None = None) -> dict:
        """Ping ``provider_id`` (or the default provider) under the budget gate.

        Raises ``ValidationError`` when no provider is configured, and
        ``BudgetExceededError`` when a hard-stop budget limit would be breached —
        the provider is not contacted in that case.
        """
        provider = (
            self.providers.get(provider_id)
            if provider_id is not None
            else self.providers.default_provider()
        )
        if provider is None:
            raise ValidationError("No provider is configured to ping.")

        inst = self.providers.instance_for(provider)

        # Budget gate — BEFORE the provider is contacted (charter §8).
        est_tokens = inst.estimate_tokens(self.PING_PROMPT) + self.PING_MAX_TOKENS
        try:
            est_cost = inst.estimate_cost(est_tokens, self.PING_MAX_TOKENS)
        except Exception:  # pragma: no cover - estimation is best-effort
            est_cost = 0.0
        decision = self.budget.check(estimated_cost=est_cost, estimated_tokens=est_tokens)
        if not decision.allowed:
            raise BudgetExceededError(decision.reason or "budget hard-stop")

        # Minimal real call.
        request = ExecutionRequest(
            messages=[Message(role="user", content=self.PING_PROMPT)],
            model=provider.active_model or provider.default_model,
            max_tokens=self.PING_MAX_TOKENS,
        )
        result = inst.execute(request)

        # Record the tiny usage so it counts against the budget like any execution.
        self.cost_engine.record(provider, result)
        self.db.flush()

        status = self.budget.status()
        return {
            "ok": result.status == "completed",
            "provider": provider.name,
            "model": result.model,
            "latency_ms": result.latency_ms,
            "prompt_tokens": result.prompt_tokens,
            "completion_tokens": result.completion_tokens,
            "total_tokens": result.total_tokens,
            "cost": result.cost,
            "currency": result.currency,
            "estimated_cost": round(est_cost, 6),
            "budget_warning": decision.warning,
            "daily_spent": status["daily_spent"],
            "monthly_spent": status["monthly_spent"],
        }

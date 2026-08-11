"""Mission Budget Envelope (WES-DEC-011) — estimate once, approve once, free run inside.

The envelope replaces per-call budget gating for mission execution:

* **Estimate at intake** — planned tasks × the measured governed-call baseline
  plus a flat reasoning overhead and a buffer (constants below are documented
  baselines from the live mission, tunable as reality updates them).
* **One approval** — the estimate rides with the plan; the Founder approves
  objective + plan + $X in a single act (``approve-plan`` with
  ``approved_budget``), which creates a ``BudgetConfig`` row scoped
  ``mission:<project_id>``. No schema change: the envelope is a scoped config
  row, and spend attribution uses the existing ``provider_usage.project_id``.
* **Free run inside** — envelope-covered execution is NOT per-call prompted and
  ignores the global per-run ``max_cost`` (retired for covered runs per
  WES-DEC-011). The meter keeps running (F6).
* **80% → notify once; 100% → hard-stop + escalation** — the six-field
  PROMPT-ESC-shaped message goes to the Founder via the platform notifier and
  the refusal reason.

Reasoning-path attribution: planning calls do not carry a work item, so
``DecompositionService`` marks the active mission with :func:`mission_context`
and the provider orchestrator's metering reads :func:`current_project_id`.
"""

from __future__ import annotations

import uuid
from contextlib import contextmanager
from contextvars import ContextVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.provider_platform import BudgetConfig, ProviderUsage

# Documented baselines (see WES-DEC-011): the governed-call figure is the live
# measurement lineage — run #2 `dbf275a6` $0.0274 (pre-SOP-library), deploy
# sample `7aa4d3a7` $0.0352 (with the ratified SOP body injected). We budget at
# the current (larger) shape. The reasoning overhead approximates the intake
# planning chain (executive pass + plan review), unmeasured pre-F6; it becomes
# a measured figure as post-F6 missions accumulate attributed usage.
GOVERNED_CALL_BASELINE_USD = 0.035
REASONING_OVERHEAD_USD = 0.20
BUFFER = 0.25

_current_project_id: ContextVar[uuid.UUID | None] = ContextVar(
    "wes_mission_project_id", default=None
)


def current_project_id() -> uuid.UUID | None:
    """The mission a reasoning call belongs to, when one is active."""
    return _current_project_id.get()


@contextmanager
def mission_context(project_id: uuid.UUID):
    """Attribute all provider calls inside the block to ``project_id``."""
    token = _current_project_id.set(project_id)
    try:
        yield
    finally:
        _current_project_id.reset(token)


# The exact width of ``budget_configs.scope`` (``String(40)``,
# app/models/provider_platform.py). F15: ``mission:<str(uuid)>`` was 44 chars and
# overflowed on Postgres at the re-release gate — SQLite fixtures don't enforce
# varchar widths, so only the real database caught it. ``mission:<uuid.hex>`` is
# 8 + 32 = 40 chars: it fits the column exactly, and the guard below makes any
# future overflow fail loudly in EVERY database, not just Postgres.
_SCOPE_COLUMN_WIDTH = 40


def _scope(project_id: uuid.UUID) -> str:
    scope = f"mission:{project_id.hex}"
    if len(scope) > _SCOPE_COLUMN_WIDTH:
        raise ValueError(
            f"envelope scope {scope!r} is {len(scope)} chars — exceeds the "
            f"budget_configs.scope column width ({_SCOPE_COLUMN_WIDTH})"
        )
    return scope


class EnvelopeExceededError(Exception):
    """Raised when a call would breach an approved mission envelope (100%)."""


class MissionBudgetService:
    def __init__(self, db: Session):
        self.db = db

    # -- estimate (intake) -------------------------------------------------

    def estimate(self, task_count: int) -> dict:
        """The intake-time envelope estimate, itemised so the Founder sees the math."""
        execution = round(task_count * GOVERNED_CALL_BASELINE_USD, 2)
        subtotal = execution + REASONING_OVERHEAD_USD
        total = round(subtotal * (1 + BUFFER), 2)
        return {
            "task_count": task_count,
            "per_call_baseline": GOVERNED_CALL_BASELINE_USD,
            "execution_estimate": execution,
            "reasoning_overhead": REASONING_OVERHEAD_USD,
            "buffer_pct": int(BUFFER * 100),
            "estimated_total": total,
            "currency": "USD",
            "ask": f"This objective, this plan, estimated ${total:.2f} — approve?",
        }

    # -- envelope lifecycle ------------------------------------------------

    def envelope(self, project_id: uuid.UUID) -> BudgetConfig | None:
        return self.db.scalar(
            select(BudgetConfig).where(BudgetConfig.scope == _scope(project_id))
        )

    def approve(self, project_id: uuid.UUID, amount: float) -> BudgetConfig:
        """Create (or update) the mission envelope — the Founder's single approval."""
        if amount <= 0:
            raise ValueError(f"envelope amount must be positive, got {amount}")
        env = self.envelope(project_id)
        if env is None:
            env = BudgetConfig(
                scope=_scope(project_id),
                max_cost=amount,
                warning_threshold=0.8,
                hard_stop=True,
            )
            self.db.add(env)
        else:
            env.max_cost = amount
            env.warning_threshold = 0.8
            env.hard_stop = True
        self.db.flush()
        return env

    def spent(self, project_id: uuid.UUID) -> float:
        return (
            self.db.scalar(
                select(func.coalesce(func.sum(ProviderUsage.estimated_cost), 0.0)).where(
                    ProviderUsage.project_id == project_id
                )
            )
            or 0.0
        )

    # -- the two triggers (80 / 100) ---------------------------------------

    def check(self, project_id: uuid.UUID, estimated_next_call: float = 0.0) -> dict:
        """Envelope status for the next call: ok | warn80 | exceeded.

        ``warn80`` fires once (dedup via a recorded provider event by the
        caller); ``exceeded`` means the caller must refuse the call, notify the
        Founder with the six-field escalation message, and pause the mission.
        """
        env = self.envelope(project_id)
        if env is None or not env.max_cost:
            return {"covered": False}
        spent = self.spent(project_id)
        projected = spent + max(estimated_next_call, 0.0)
        threshold = env.warning_threshold or 0.8
        status = "ok"
        if projected >= env.max_cost:
            status = "exceeded"
        elif projected >= env.max_cost * threshold:
            status = "warn80"
        return {
            "covered": True,
            "status": status,
            "amount": env.max_cost,
            "spent": round(spent, 6),
            "projected": round(projected, 6),
            "pct": round(projected / env.max_cost, 3),
        }

    @staticmethod
    def escalation_message(project_code: str, check: dict) -> str:
        """The PROMPT-ESC six-field package for the 100% hard-stop."""
        return (
            f"ESCALATION — mission budget envelope exhausted.\n"
            f"1. Issue: mission {project_code} reached 100% of its approved envelope "
            f"(${check.get('spent', 0):.4f} of ${check.get('amount', 0):.2f}).\n"
            f"2. Severity: high — execution hard-stopped, mission paused.\n"
            f"3. Evidence: provider_usage attributed to the mission; projected next call "
            f"${check.get('projected', 0):.4f} ({check.get('pct', 0):.0%}).\n"
            f"4. Options considered: (a) Founder raises the envelope; (b) Founder ends the "
            f"mission here; (c) descope remaining tasks and re-estimate.\n"
            f"5. Recommendation: Founder decision — the envelope is a Founder instrument "
            f"(WES-DEC-011).\n"
            f"6. Expected outcome: mission resumes only on a new approved amount."
        )

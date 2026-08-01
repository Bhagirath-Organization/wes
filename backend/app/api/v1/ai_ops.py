"""AI Operations dashboard (Phase C) — admin-only.

Surfaces the AI Provider Orchestrator's internals: provider health, the capability
registry, routing decisions, fallback events, consensus outcomes, cost/latency and
learning trends. This is the ADMIN view; the Founder never sees any of it.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permission
from app.domain.roles import Permission
from app.services.provider_orchestrator import AIProviderOrchestrator

router = APIRouter(prefix="/ai-ops", tags=["ai-ops"])
_read = Depends(require_permission(Permission.DASHBOARD_READ))


@router.get("/dashboard", dependencies=[_read])
def ai_ops_dashboard(db: Session = Depends(get_db)) -> dict:
    """Provider health, capability registry, routing/fallback, learning trends."""
    return {"data": AIProviderOrchestrator(db).dashboard()}


@router.get("/capabilities", dependencies=[_read])
def capability_registry(db: Session = Depends(get_db)) -> dict:
    """Every provider's capability card + live health + learned reliability."""
    return {"data": AIProviderOrchestrator(db).capability_registry()}


@router.get("/benchmark", dependencies=[_read])
def benchmark(db: Session = Depends(get_db)) -> dict:
    """Lightweight health/latency probe of each enabled provider."""
    return {"data": AIProviderOrchestrator(db).benchmark()}


@router.get("/evolution/backlog", dependencies=[_read])
def evolution_backlog(db: Session = Depends(get_db)) -> dict:
    """Company Evolution Backlog — all improvement proposals, ranked by business value."""
    from app.services.company_evolution import CompanyEvolutionService

    svc = CompanyEvolutionService(db)
    return {"data": {"score": svc.evolution_score(), "backlog": svc.backlog()}}


@router.get("/evolution/audit", dependencies=[_read])
def evolution_audit(db: Session = Depends(get_db)) -> dict:
    """Live self-audit findings (evidence-based), without persisting proposals."""
    from app.services.company_evolution import CompanyEvolutionService

    return {"data": CompanyEvolutionService(db).audit()}


@router.post("/evolution/run", dependencies=[_read])
def evolution_run(debate_top: int = 0, db: Session = Depends(get_db)) -> dict:
    """Run one continuous-evolution cycle: observe -> propose -> optionally debate."""
    from app.services.company_evolution import CompanyEvolutionService

    return {"data": CompanyEvolutionService(db).run_cycle(debate_top=debate_top)}


@router.get("/route", dependencies=[_read])
def preview_route(task: str, db: Session = Depends(get_db)) -> dict:
    """Preview which provider the Brain would select for a task type (no execution)."""
    orch = AIProviderOrchestrator(db)
    task_type = orch.classify(task)
    d = orch.route(task_type)
    return {"data": {
        "task_input": task, "task_type": task_type, "best": d.best,
        "alternative": d.alternative, "fallback": d.fallback, "reason": d.reason,
        "confidence": d.confidence, "est_cost": d.est_cost,
        "est_latency_ms": d.est_latency_ms, "order": d.order,
    }}

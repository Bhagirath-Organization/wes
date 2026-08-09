"""AI Provider Orchestrator (Phase C).

The Company Brain owns the intelligence; providers are interchangeable execution
engines. Every reasoning request routes through here, which:

* classifies the task,
* scores every ENABLED provider by capability-for-task + live health + learned
  success/latency (the Provider Learning Engine, from ``provider_routing_log``),
* picks best / alternative / fallback with a reason, confidence, and cost/latency
  estimate (Automatic Routing Engine),
* executes with Automatic Fallback on failure/timeout/low-confidence,
* can run the same task across several providers and combine them (Consensus
  Engine),
* records every decision for the AI Operations dashboard and future routing.

Reuses ``ProviderService`` for the registry, health, config and execution — no
provider-specific logic lives in the executives, and none is duplicated here. The
Founder never sees any of this; only the admin AI-Ops dashboard does.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.provider_routing import ProviderRoutingLog
from app.providers import ExecutionRequest

# --- Capability Registry ---------------------------------------------------
# Factual provider characteristics (context, quality tiers, cost, latency, vision,
# tools). Reference data, not reasoning. Live health and learned stats are layered
# on top at routing time. Unknown providers fall back to a neutral profile so the
# architecture stays provider-independent.
_NEUTRAL = {"strengths": [], "context": 32000, "reasoning": 0.75, "coding": 0.75,
            "cost": 0.3, "latency_tier": 2, "vision": False, "tools": False}

CAPABILITY_PROFILES: dict[str, dict] = {
    "claude": {"strengths": ["reasoning", "coding", "architecture", "writing", "tools"],
               "context": 200000, "reasoning": 0.96, "coding": 0.95, "cost": 0.6,
               "latency_tier": 2, "vision": True, "tools": True},
    "openai": {"strengths": ["reasoning", "coding", "vision", "tools"],
               "context": 128000, "reasoning": 0.90, "coding": 0.90, "cost": 0.6,
               "latency_tier": 2, "vision": True, "tools": True},
    "gemini": {"strengths": ["reasoning", "vision", "research", "long_context"],
               "context": 1000000, "reasoning": 0.88, "coding": 0.82, "cost": 0.4,
               "latency_tier": 2, "vision": True, "tools": True},
    "deepseek": {"strengths": ["coding", "reasoning", "math"],
                 "context": 64000, "reasoning": 0.88, "coding": 0.92, "cost": 0.1,
                 "latency_tier": 2, "vision": False, "tools": True},
    "qwen": {"strengths": ["coding", "reasoning", "multilingual"],
             "context": 32000, "reasoning": 0.82, "coding": 0.85, "cost": 0.05,
             "latency_tier": 3, "vision": False, "tools": False},
    "ollama": {"strengths": ["local", "private", "cost_free"],
               "context": 32000, "reasoning": 0.72, "coding": 0.72, "cost": 0.0,
               "latency_tier": 3, "vision": False, "tools": False},
    "llama": {"strengths": ["local", "open"],
              "context": 32000, "reasoning": 0.72, "coding": 0.72, "cost": 0.0,
              "latency_tier": 3, "vision": False, "tools": False},
    "openrouter": {"strengths": ["gateway", "flexible"],
                   "context": 128000, "reasoning": 0.85, "coding": 0.85, "cost": 0.5,
                   "latency_tier": 2, "vision": True, "tools": True},
    "mock": {"strengths": ["deterministic", "testing"],
             "context": 8000, "reasoning": 0.30, "coding": 0.30, "cost": 0.0,
             "latency_tier": 1, "vision": False, "tools": False},
}

# Which capability dimension each task type primarily needs.
_TASK_DIMENSION = {
    "business_strategy": "reasoning", "architecture": "reasoning", "planning": "reasoning",
    "reasoning": "reasoning", "review": "reasoning", "security": "reasoning",
    "research": "reasoning", "domain_understanding": "reasoning",
    "coding": "coding", "testing": "coding", "documentation": "reasoning",
    "vision": "reasoning", "deployment": "reasoning", "knowledge_retrieval": "reasoning",
}

# Keyword hints for automatic task classification.
_CLASSIFY = [
    ("coding", ("implement", "code", "file blocks", "<<<file", "function", "refactor", "bug")),
    ("testing", ("test", "pytest", "regression", "coverage")),
    ("security", ("security", "vulnerab", "threat", "secret", "compliance", "privacy")),
    ("architecture", ("architect", "design the system", "components", "pattern", "dependenc")),
    ("business_strategy", ("business", "ceo", "roi", "market", "customer", "vision", "growth")),
    ("domain_understanding", ("industry", "domain", "stakeholder", "business model", "workflow")),
    ("planning", ("milestone", "sprint", "plan", "task breakdown", "roadmap")),
    ("documentation", ("document", "readme", "notes", "write up")),
    ("review", ("review", "verdict", "approve", "changes_requested")),
]


@dataclass
class RouteDecision:
    task_type: str
    best: str | None
    alternative: str | None
    fallback: str | None
    reason: str
    confidence: float
    est_cost: float
    est_latency_ms: int
    order: list[str] = field(default_factory=list)   # full attempt order (provider names)
    scores: dict = field(default_factory=dict)


class AIProviderOrchestrator:
    _LAT_MS = {1: 800, 2: 4000, 3: 30000}  # latency tier -> rough estimate

    def __init__(self, db: Session):
        self.db = db
        from app.services.provider_platform import CostEngine
        from app.services.providers_service import ProviderService

        self.providers = ProviderService(db)
        # F6 (WES-DEC-010 step 4): every successful provider execution routed
        # through this orchestrator — the executive-reasoning, dev-generation
        # and consensus paths — records real usage so budget counters see it.
        self.cost_engine = CostEngine(db)

    # -- capability registry (static + live health + learned) --------------

    @staticmethod
    def profile(name: str) -> dict:
        return {**_NEUTRAL, **CAPABILITY_PROFILES.get((name or "").lower(), {})}

    def capability_registry(self) -> list[dict]:
        """Every provider's capability card + live health + learned reliability."""
        health = {h["name"]: h for h in self._safe_health()}
        cards = []
        for p in self.providers.list_providers():
            prof = self.profile(p.name)
            stats = self.learned_stats(p.name)
            cards.append({
                "provider": p.name,
                "enabled": p.enabled,
                "is_default": p.is_default,
                "capabilities": prof["strengths"],
                "context_size": prof["context"],
                "reasoning_quality": prof["reasoning"],
                "coding_quality": prof["coding"],
                "cost": prof["cost"],
                "vision": prof["vision"],
                "tools": prof["tools"],
                "latency_tier": prof["latency_tier"],
                "health": health.get(p.name, {}).get("status", "unknown"),
                "reliability": stats["success_rate"],
                "avg_latency_ms": stats["avg_latency_ms"],
                "requests": stats["requests"],
            })
        return cards

    def _safe_health(self) -> list[dict]:
        try:
            return self.providers.check_health()
        except Exception:
            return []

    def learned_stats(self, provider: str) -> dict:
        """Provider Learning Engine: success rate + avg latency from real history."""
        rows = self.db.execute(
            select(ProviderRoutingLog.success, ProviderRoutingLog.actual_latency_ms)
            .where(ProviderRoutingLog.chosen_provider == provider)
            .order_by(ProviderRoutingLog.created_at.desc()).limit(200)
        ).all()
        if not rows:
            return {"success_rate": None, "avg_latency_ms": None, "requests": 0}
        ok = sum(1 for s, _ in rows if s)
        lats = [lat for _, lat in rows if lat]
        return {
            "success_rate": round(ok / len(rows), 3),
            "avg_latency_ms": int(sum(lats) / len(lats)) if lats else None,
            "requests": len(rows),
        }

    # -- task classification ----------------------------------------------

    @staticmethod
    def classify(task_hint: str | None = None, text: str = "") -> str:
        hint = (task_hint or "").lower()
        if hint in _TASK_DIMENSION:
            return hint
        hay = f"{hint} {text}".lower()
        for task, kws in _CLASSIFY:
            if any(k in hay for k in kws):
                return task
        return "reasoning"

    # -- automatic routing -------------------------------------------------

    def route(self, task_type: str, *, prefer: str | None = None) -> RouteDecision:
        """Score enabled providers for this task and pick best/alt/fallback."""
        dim = _TASK_DIMENSION.get(task_type, "reasoning")
        health = {h["name"]: h.get("status") for h in self._safe_health()}
        scored: list[tuple[float, str]] = []
        for p in self.providers.list_providers():
            if not p.enabled:
                continue
            prof = self.profile(p.name)
            stats = self.learned_stats(p.name)
            quality = float(prof.get(dim, 0.75))
            # health: unavailable providers are dropped; degraded penalised.
            hstatus = health.get(p.name, "unknown")
            if hstatus == "unavailable":
                continue
            score = quality
            score += 0.15 if p.is_default else 0.0
            score -= 0.05 * (prof["latency_tier"] - 1)          # prefer faster
            score -= 0.10 * prof["cost"]                        # prefer cheaper
            if stats["success_rate"] is not None:               # learned reliability
                score += 0.20 * (stats["success_rate"] - 0.5)
            if hstatus == "degraded":
                score -= 0.15
            if prefer and p.name == prefer:                     # role-mapping hint
                score += 0.10
            scored.append((round(score, 4), p.name))
        scored.sort(key=lambda s: -s[0])

        if not scored:
            # No capability-scored provider — fall back to the registry default so
            # behaviour is never worse than before this engine existed.
            default = self.providers.default_provider()
            name = default.name if default else None
            return RouteDecision(task_type, name, None, None,
                                 "default provider (no enabled capability match)",
                                 0.3 if name else 0.0, 0.0, self._LAT_MS[3],
                                 order=[name] if name else [])
        order = [n for _, n in scored]
        best = order[0]
        prof = self.profile(best)
        top = scored[0][0]
        runner = scored[1][0] if len(scored) > 1 else 0.0
        confidence = round(min(1.0, 0.55 + max(0.0, top - runner)), 2)
        reason = (f"'{best}' scored highest for {task_type} "
                  f"({_TASK_DIMENSION.get(task_type,'reasoning')} quality "
                  f"{prof.get(dim):.2f}, cost {prof['cost']}, health "
                  f"{health.get(best,'unknown')})")
        return RouteDecision(
            task_type=task_type, best=best,
            alternative=order[1] if len(order) > 1 else None,
            fallback=order[-1] if len(order) > 1 else None,
            reason=reason, confidence=confidence,
            est_cost=round(prof["cost"], 3),
            est_latency_ms=self._LAT_MS[prof["latency_tier"]],
            order=order, scores=dict(scored and [(n, s) for s, n in scored]),
        )

    # -- execution with automatic fallback ---------------------------------

    def execute(self, request: ExecutionRequest, *, task_type: str | None = None,
                prefer: str | None = None):
        """Route + execute with automatic fallback. Returns (result, provider_name).

        Tries best -> alternative -> ... in score order; a provider that raises,
        times out, or reports ``status == 'failed'`` triggers the next. Every
        attempt path is recorded for learning and the AI-Ops dashboard.
        """
        task_type = task_type or self.classify(None, request.as_text() if hasattr(request, "as_text") else "")
        decision = self.route(task_type, prefer=prefer)
        if not decision.order:
            raise RuntimeError(f"No provider available for task '{task_type}'")

        started = time.perf_counter()
        attempts = 0
        last_error: Exception | None = None
        used: str | None = None
        used_row = None
        result = None
        for name in decision.order:
            attempts += 1
            row = self.providers.get_by_name(name)
            if row is None:
                continue
            try:
                inst = self.providers.instance_for(row)
                result = inst.execute(request)
                if getattr(result, "status", "completed") == "failed":
                    last_error = RuntimeError(getattr(result, "error", "failed"))
                    continue
                used = name
                used_row = row
                break
            except Exception as exc:  # provider failure -> fall back
                last_error = exc
                continue
        actual_ms = int((time.perf_counter() - started) * 1000)

        self._log(decision, used=used, attempts=attempts, actual_ms=actual_ms,
                  success=used is not None,
                  error=None if used else str(last_error)[:300])

        if used is None:
            raise RuntimeError(
                f"All providers failed for '{task_type}' (tried {attempts}): {last_error}"
            )
        # F6: record the real spend of this reasoning call (ProviderUsage +
        # billing rollups), exactly like the orchestration pipeline does. No
        # ExecutionRun exists on this path, so run_id stays None. Caveat
        # (documented in the PR): recording shares the caller's transaction —
        # a later rollback discards it with everything else.
        self.cost_engine.record(used_row, result)
        return result, used

    # -- consensus across multiple providers -------------------------------

    def consensus(self, request: ExecutionRequest, *, task_type: str, k: int = 3) -> dict:
        """Run the same request across the top-k enabled providers and combine.

        Returns each provider's answer, a confidence-weighted view, and whether
        the providers conflicted (for executive/Founder escalation).
        """
        decision = self.route(task_type)
        providers = decision.order[:k]
        answers = []
        for name in providers:
            row = self.providers.get_by_name(name)
            if row is None:
                continue
            try:
                r = row and self.providers.instance_for(row).execute(request)
                ok = getattr(r, "status", "completed") != "failed"
                if r is not None and ok:
                    # F6: consensus calls are real spend too — meter each success.
                    self.cost_engine.record(row, r)
                answers.append({"provider": name, "output": getattr(r, "output", ""),
                                "latency_ms": getattr(r, "latency_ms", None),
                                "ok": ok})
            except Exception as exc:
                answers.append({"provider": name, "output": "", "ok": False,
                                "error": str(exc)[:200]})
        ok = [a for a in answers if a["ok"] and a["output"].strip()]
        conflict = len({a["output"].strip()[:200] for a in ok}) > 1 if len(ok) > 1 else False
        self._log(decision, used=(ok[0]["provider"] if ok else None),
                  attempts=len(answers), actual_ms=0, success=bool(ok),
                  decision_kind="consensus")
        return {
            "task_type": task_type,
            "providers": providers,
            "answers": answers,
            "agreement": "conflict" if conflict else ("unanimous" if len(ok) > 1 else "single"),
            "conflict": conflict,
            "recommended": ok[0] if ok else None,
            "note": ("Providers disagree — escalate to the executive board / Founder."
                     if conflict else "Providers agree." if len(ok) > 1 else
                     "Single provider available."),
        }

    # -- benchmark ---------------------------------------------------------

    def benchmark(self) -> list[dict]:
        """Lightweight health/latency probe of each enabled provider."""
        out = []
        for p in self.providers.list_providers():
            if not p.enabled:
                out.append({"provider": p.name, "enabled": False, "status": "disabled"})
                continue
            t = time.perf_counter()
            try:
                h = self.providers.instance_for(p).health()
                out.append({"provider": p.name, "enabled": True,
                            "status": getattr(h, "status", "unknown"),
                            "probe_ms": int((time.perf_counter() - t) * 1000)})
            except Exception as exc:
                out.append({"provider": p.name, "enabled": True, "status": "unavailable",
                            "error": str(exc)[:150]})
        return out

    # -- persistence -------------------------------------------------------

    def _log(self, d: RouteDecision, *, used, attempts, actual_ms, success,
             error=None, decision_kind="route"):
        try:
            self.db.add(ProviderRoutingLog(
                task_type=d.task_type,
                decision="fallback" if (success and used and used != d.best) else decision_kind,
                chosen_provider=used or (d.best or "none"),
                alternative_provider=d.alternative, fallback_provider=d.fallback,
                reason=d.reason, confidence=d.confidence, est_cost=d.est_cost,
                est_latency_ms=d.est_latency_ms, actual_latency_ms=actual_ms or None,
                fallback_used=bool(used and used != d.best), attempts=attempts,
                success=success, error=error,
            ))
            self.db.flush()
        except Exception:
            pass

    # -- admin AI-Ops dashboard aggregate ----------------------------------

    def dashboard(self) -> dict:
        recent = self.db.scalars(
            select(ProviderRoutingLog).order_by(ProviderRoutingLog.created_at.desc()).limit(20)
        ).all()
        total = self.db.scalar(select(func.count(ProviderRoutingLog.id))) or 0
        fallbacks = self.db.scalar(
            select(func.count(ProviderRoutingLog.id)).where(ProviderRoutingLog.fallback_used.is_(True))
        ) or 0
        by_task = self.db.execute(
            select(ProviderRoutingLog.task_type, ProviderRoutingLog.chosen_provider,
                   func.count(ProviderRoutingLog.id))
            .group_by(ProviderRoutingLog.task_type, ProviderRoutingLog.chosen_provider)
        ).all()
        return {
            "provider_health": self.benchmark(),
            "capability_registry": self.capability_registry(),
            "routing": {
                "total_decisions": total,
                "fallback_events": fallbacks,
                "fallback_rate": round(fallbacks / total, 3) if total else 0.0,
                "by_task_provider": [
                    {"task_type": t, "provider": p, "count": c} for t, p, c in by_task
                ],
                "recent_decisions": [
                    {"task_type": r.task_type, "decision": r.decision,
                     "chosen": r.chosen_provider, "alternative": r.alternative_provider,
                     "fallback_used": r.fallback_used, "confidence": r.confidence,
                     "success": r.success, "actual_latency_ms": r.actual_latency_ms,
                     "reason": r.reason}
                    for r in recent
                ],
            },
            "learning_trends": [
                {"provider": c["provider"], "reliability": c["reliability"],
                 "avg_latency_ms": c["avg_latency_ms"], "requests": c["requests"]}
                for c in self.capability_registry() if c["enabled"]
            ],
        }

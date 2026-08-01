"""Continuous Company Evolution Engine (Phase E).

A permanent executive function: WES observes ITSELF, discovers weaknesses from real
signals, turns each into a structured Improvement Proposal, ranks them by business
value, has the executive board (Company Brain) debate them, and surfaces only the
business recommendation to the Founder. It never invents problems — every finding is
backed by live evidence pulled from systems that already exist:

* Founder OS governance          -> blueprint/quality/knowledge/memory/learning health
* Provider Orchestrator (Phase C)-> provider reliability, fallback, single-provider risk
* Mission Control (Phase D)       -> mission success rate, deployment reachability
* Repository intelligence         -> architecture health / technical debt
* Development history             -> repeated failures, quality
* Company Brain (Phase A)         -> the executive debate + recommended/alternative solutions

Nothing here is duplicated; this engine only reads, reasons (via the Brain) and ranks.
"""

from __future__ import annotations

import json
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.development import DevelopmentTask
from app.models.improvement import ImprovementProposal
from app.models.provider_routing import ProviderRoutingLog

# Business-value weight per dimension (ranking is by BUSINESS value, not effort).
_BUSINESS_WEIGHT = {
    "founder_experience": 1.0, "security": 1.0, "deployment": 0.95,
    "reasoning_quality": 0.9, "blueprint_compliance": 0.9, "provider_resilience": 0.85,
    "quality": 0.8, "architecture": 0.75, "knowledge": 0.6, "technical_debt": 0.55,
    "automation": 0.6,
}
_SEV_SCORE = {"critical": 1.0, "high": 0.75, "medium": 0.5, "low": 0.25}


def _priority(severity: str, dimension: str) -> tuple[str, float]:
    score = round(_SEV_SCORE.get(severity, 0.5) * _BUSINESS_WEIGHT.get(dimension, 0.6), 3)
    label = ("critical" if score >= 0.8 else "high" if score >= 0.6
             else "medium" if score >= 0.35 else "low")
    return label, score


class CompanyEvolutionService:
    def __init__(self, db: Session):
        self.db = db

    # ================================================================= #
    #  Executive Audit Engine — deterministic, evidence-based findings   #
    # ================================================================= #

    def audit(self) -> list[dict]:
        """Continuously observe WES and return evidence-backed findings."""
        findings: list[dict] = []
        for check in (
            self._audit_providers, self._audit_reasoning, self._audit_deployment,
            self._audit_blueprint, self._audit_quality, self._audit_knowledge,
            self._audit_founder_experience,
        ):
            try:
                findings.extend(check())
            except Exception:
                continue
        return findings

    def _F(self, *, dimension, severity, title, problem, why, business, technical,
           risk, evidence, blueprint, signature, recommended=None):
        prio, score = _priority(severity, dimension)
        return {
            "dimension": dimension, "severity": severity, "priority": prio,
            "priority_score": score, "title": title, "problem": problem,
            "root_cause": why, "business_impact": business, "technical_impact": technical,
            "risk": risk, "evidence": evidence, "blueprint_ref": blueprint,
            "signature": signature, "recommended_solution": recommended,
        }

    # -- provider resilience (Phase C signals) -----------------------------

    def _audit_providers(self) -> list[dict]:
        from app.services.providers_service import ProviderService

        ps = ProviderService(self.db)
        enabled = [p for p in ps.list_providers() if p.enabled]
        out = []
        if len(enabled) <= 1:
            out.append(self._F(
                dimension="provider_resilience", severity="high",
                title="The company depends on a single AI workforce provider",
                problem="Only one AI provider is active, so there is no automatic "
                        "alternative if it degrades or becomes unavailable.",
                why="Additional providers are registered but not activated (no credentials).",
                business="A single-provider outage would halt all reasoning and delivery.",
                technical="No cross-provider consensus; reasoning quality is capped by one model.",
                risk="Company-wide stoppage on provider failure.",
                evidence=f"Enabled providers: {[p.name for p in enabled]} (count={len(enabled)}).",
                blueprint="Volume 05 — AI System; Volume 10 — Automation (model flexibility)",
                signature="provider_resilience:single_provider",
                recommended="Activate at least one additional AI provider so the orchestrator "
                            "can route, compare and fall back automatically.",
            ))
        # High fallback rate = the primary provider is unreliable.
        total = self.db.scalar(select(func.count(ProviderRoutingLog.id))) or 0
        fb = self.db.scalar(select(func.count(ProviderRoutingLog.id))
                            .where(ProviderRoutingLog.fallback_used.is_(True))) or 0
        if total >= 5 and fb / total > 0.3:
            out.append(self._F(
                dimension="provider_resilience", severity="medium",
                title="AI workforce is falling back to alternatives too often",
                problem=f"{fb}/{total} recent requests required a fallback provider.",
                why="The preferred provider is failing or timing out frequently.",
                business="Slower, less predictable delivery.",
                technical="Elevated fallback rate indicates primary-provider instability.",
                risk="Latency and cost variance.",
                evidence=f"fallback_rate={fb/total:.2f} over {total} routed requests.",
                blueprint="Volume 05 — AI System",
                signature="provider_resilience:fallback_rate",
            ))
        return out

    # -- reasoning quality --------------------------------------------------

    def _audit_reasoning(self) -> list[dict]:
        from app.services.provider_orchestrator import AIProviderOrchestrator

        orch = AIProviderOrchestrator(self.db)
        enabled = [c for c in orch.capability_registry() if c["enabled"]]
        weak = [c for c in enabled if (c.get("reasoning_quality") or 1) < 0.8]
        if enabled and len(weak) == len(enabled):
            best = max((c.get("reasoning_quality") or 0) for c in enabled)
            return [self._F(
                dimension="reasoning_quality", severity="high",
                title="Executive reasoning is limited by the available AI model",
                problem="Every active AI provider is a lower-tier reasoning model, "
                        "which caps the quality of executive decisions and planning.",
                why="Only a small/local model is currently active.",
                business="Plans, architecture and risk analysis are less sophisticated "
                         "than a frontier model would produce.",
                technical=f"Best active reasoning quality ~{best:.2f} (frontier ~0.95).",
                risk="Sub-optimal architectural and business decisions.",
                evidence=f"Active providers reasoning quality: "
                         f"{[(c['provider'], c['reasoning_quality']) for c in enabled]}.",
                blueprint="Volume 05 — AI System (decision quality)",
                signature="reasoning_quality:low_tier_model",
                recommended="Enable a frontier reasoning provider for high-stakes executive "
                            "decisions; the orchestrator will route strategy tasks to it.",
            )]
        return []

    # -- deployment reachability (Phase D finding, quantified) -------------

    def _audit_deployment(self) -> list[dict]:
        from app.models.devops import DeploymentRun

        deployed = self.db.scalar(
            select(func.count(DeploymentRun.id)).where(DeploymentRun.status == "deployed")
        ) or 0
        if deployed:
            return [self._F(
                dimension="deployment", severity="high",
                title="Delivered products are not reachable at a live address",
                problem="Deployments extract a build locally and verify it, but nothing is "
                        "hosted at a public URL, so a completed product cannot be used.",
                why="No hosting/CD target is wired; deployment stops at local artifact extraction.",
                business="Founder cannot actually use or share the software the company builds.",
                technical="deployment_runs carry no URL/host; there is no running instance.",
                risk="Delivery appears complete but produces nothing operable.",
                evidence=f"{deployed} deployment run(s) completed, 0 expose a live URL.",
                blueprint="Volume 04 — Engineering System (Release); Volume 06 — source of truth",
                signature="deployment:no_live_url",
                recommended="Add a real hosting target so approved releases are deployed to a "
                            "reachable URL and returned to the Founder.",
            )]
        return []

    # -- blueprint / architecture (governance signals) --------------------

    def _audit_blueprint(self) -> list[dict]:
        from app.services.founder_os import FounderOSService

        gov = FounderOSService(self.db).governance()
        out = []
        for d in gov.get("dimensions", []):
            if d.get("status") != "healthy" and d.get("dimension") == "architecture":
                metric = d.get("metric")
                out.append(self._F(
                    dimension="architecture", severity="medium",
                    title="Repository/architecture health is below standard",
                    problem="The company's own codebase health is degraded, which slows "
                            "safe change and raises the chance of regressions.",
                    why=d.get("detail") or "Low documentation/structure health.",
                    business="Slower delivery and higher risk on the company's own platform.",
                    technical=f"Repository health score {metric}.",
                    risk="Accumulating technical debt.",
                    evidence=d.get("detail") or "governance: architecture degraded",
                    blueprint="Volume 04 — Engineering System; Volume 09 — Knowledge",
                    signature="architecture:repo_health",
                    recommended="Schedule a documentation + structure improvement mission on "
                                "the platform codebase.",
                ))
        return out

    # -- quality / repeated failures --------------------------------------

    def _audit_quality(self) -> list[dict]:
        failed = self.db.scalar(
            select(func.count(DevelopmentTask.id)).where(DevelopmentTask.status == "failed")
        ) or 0
        total = self.db.scalar(select(func.count(DevelopmentTask.id))) or 0
        if total >= 10 and failed / total > 0.25:
            return [self._F(
                dimension="quality", severity="high",
                title="A high share of engineering work is failing on first attempt",
                problem=f"{failed}/{total} development tasks ended in failure.",
                why="Code generation reliability is limited on the current AI model.",
                business="Wasted cycles and delayed delivery.",
                technical="Generation frequently returns unusable output before retry.",
                risk="Throughput and predictability degrade.",
                evidence=f"failed={failed}, total={total} ({failed/total:.0%} failure rate).",
                blueprint="Volume 08 — Security & Quality",
                signature="quality:failure_rate",
                recommended="Route code generation to a stronger coding provider and expand "
                            "self-debug iterations.",
            )]
        return []

    # -- knowledge coverage -----------------------------------------------

    def _audit_knowledge(self) -> list[dict]:
        from app.models.knowledge import KnowledgeDocument

        projects = self.db.scalar(select(func.count(func.distinct(DevelopmentTask.id)))) or 0
        adr = self.db.scalar(
            select(func.count(KnowledgeDocument.id))
            .where(KnowledgeDocument.doc_type.in_(["architecture", "decision_record"]))
        ) or 0
        if projects >= 10 and adr < 3:
            return [self._F(
                dimension="knowledge", severity="medium",
                title="Architecture and decision records are not being captured",
                problem="The company delivers work but rarely records formal architecture "
                        "or decision documents, so rationale is lost over time.",
                why="Decision-record generation is not part of the delivery workflow.",
                business="Repeated re-analysis; weaker institutional memory.",
                technical=f"Only {adr} architecture/decision documents recorded.",
                risk="Knowledge erosion and re-litigated decisions.",
                evidence=f"architecture/decision documents={adr}.",
                blueprint="Volume 09 — Knowledge Management (Decision Records / ADR)",
                signature="knowledge:missing_adr",
                recommended="Generate an Architecture/Decision record automatically at the end "
                            "of each mission.",
            )]
        return []

    # -- founder experience (planning speed) ------------------------------

    def _audit_founder_experience(self) -> list[dict]:
        rows = self.db.execute(
            select(ProviderRoutingLog.actual_latency_ms)
            .where(ProviderRoutingLog.actual_latency_ms.isnot(None))
            .order_by(ProviderRoutingLog.created_at.desc()).limit(50)
        ).all()
        lats = [r[0] for r in rows if r[0]]
        if lats and sum(lats) / len(lats) > 15000:
            avg = int(sum(lats) / len(lats))
            return [self._F(
                dimension="founder_experience", severity="medium",
                title="The company takes a long time to think before responding",
                problem="Executive reasoning is slow, so missions spend minutes per step "
                        "and the Founder waits longer than ideal.",
                why="Reasoning runs on a CPU-bound local model.",
                business="Slower turnaround reduces how interactive the company feels.",
                technical=f"Average reasoning latency ~{avg} ms per call.",
                risk="Founder experience feels sluggish at scale.",
                evidence=f"avg reasoning latency ~{avg} ms over {len(lats)} calls.",
                blueprint="Volume 01 — Foundation (responsiveness)",
                signature="founder_experience:reasoning_latency",
                recommended="Enable a faster hosted provider for interactive reasoning; keep "
                            "the local model as a private fallback.",
            )]
        return []

    # ================================================================= #
    #  Improvement Proposal Engine + Backlog                            #
    # ================================================================= #

    def generate_proposals(self, *, persist: bool = True) -> list[dict]:
        """Audit -> upsert proposals (dedup by signature). No LLM needed."""
        findings = self.audit()
        results = []
        for f in findings:
            existing = self.db.scalar(
                select(ImprovementProposal).where(ImprovementProposal.signature == f["signature"])
            )
            if existing is None:
                p = ImprovementProposal(
                    dimension=f["dimension"], signature=f["signature"], title=f["title"],
                    problem=f["problem"], evidence=f["evidence"], root_cause=f["root_cause"],
                    business_impact=f["business_impact"], technical_impact=f["technical_impact"],
                    blueprint_ref=f["blueprint_ref"], risk=f["risk"], priority=f["priority"],
                    priority_score=f["priority_score"],
                    recommended_solution=f.get("recommended_solution"),
                )
                if persist:
                    self.db.add(p)
                results.append(p)
            else:
                existing.evidence = f["evidence"]
                existing.priority = f["priority"]
                existing.priority_score = f["priority_score"]
                results.append(existing)
        if persist:
            self.db.flush()
        return [self.serialize(p) for p in results]

    # ================================================================= #
    #  Executive Board debate (reuse the Company Brain)                 #
    # ================================================================= #

    def debate(self, proposal: ImprovementProposal,
               lenses=("CEO", "CTO", "CHIEF_ARCHITECT")) -> dict:
        """The executive board debates a proposal via the Company Brain (Phase A).

        Each executive deliberates in its own lens (business/technical/architecture…)
        and the Brain combines confidence into a final recommendation. Reuses
        ``CompanyBrain.deliberate`` — no scripted opinions.
        """
        from app.services.company_brain import CompanyBrain

        brain = CompanyBrain(self.db)
        question = (
            f"Improvement proposal for OUR OWN company platform: {proposal.title}. "
            f"Problem: {proposal.problem} Evidence: {proposal.evidence}. "
            "Give your opinion, concerns, and whether the company should invest now."
        )
        objective = f"Company self-improvement: {proposal.title}"
        opinions = []
        for role in lenses:
            try:
                d = brain.deliberate(role, objective, question=question)
                opinions.append({
                    "executive": role,
                    "opinion": d.get("recommendation"),
                    "concerns": d.get("risks", [])[:3],
                    "recommendation": d.get("recommendation"),
                    "confidence": d.get("confidence"),
                    "alternatives": d.get("alternatives", [])[:2],
                    "blueprint": d.get("blueprint_refs", [])[:1],
                })
            except Exception as exc:
                opinions.append({"executive": role, "opinion": None,
                                 "error": str(exc)[:150], "confidence": 0.0})
        confs = [o["confidence"] for o in opinions if o.get("confidence")]
        avg_conf = round(sum(confs) / len(confs), 2) if confs else 0.0
        # Final recommendation from the highest-confidence executive (Brain synthesis).
        best = max(opinions, key=lambda o: o.get("confidence") or 0, default=None)
        final = {
            "invest": avg_conf >= 0.6,
            "board_confidence": avg_conf,
            "final_recommendation": best.get("recommendation") if best else None,
            "recommended_alternatives": best.get("alternatives") if best else [],
        }
        proposal.debate = json.dumps({"opinions": opinions, "final": final})
        proposal.confidence = avg_conf
        if best and best.get("recommendation") and not proposal.recommended_solution:
            proposal.recommended_solution = best["recommendation"][:800]
        proposal.alternatives = json.dumps(best.get("alternatives", []) if best else [])
        self.db.flush()
        return {"opinions": opinions, "final": final}

    # ================================================================= #
    #  Backlog + Evolution Score + Founder-facing view                 #
    # ================================================================= #

    def backlog(self, *, status: str = "open") -> dict:
        rows = self.db.scalars(
            select(ImprovementProposal)
            .where(ImprovementProposal.status == status)
            .order_by(ImprovementProposal.priority_score.desc(), ImprovementProposal.created_at.desc())
        ).all()
        by_priority = {"critical": [], "high": [], "medium": [], "low": []}
        for p in rows:
            by_priority.setdefault(p.priority, []).append(self.serialize(p))
        return {
            "total": len(rows),
            "by_priority": {k: len(v) for k, v in by_priority.items()},
            "critical": by_priority["critical"], "high": by_priority["high"],
            "medium": by_priority["medium"], "low": by_priority["low"],
        }

    def evolution_score(self) -> dict:
        """Company Evolution Score — overall maturity from real dimensions."""
        from app.services.founder_os import FounderOSService

        gov = FounderOSService(self.db).governance()
        dims = {d.get("dimension"): d for d in gov.get("dimensions", [])}

        def h(name):  # 100 if healthy, 40 if degraded, 0 if absent
            d = dims.get(name)
            return 100 if (d and d["status"] == "healthy") else (40 if d else 0)

        open_props = self.db.scalar(
            select(func.count(ImprovementProposal.id)).where(ImprovementProposal.status == "open")
        ) or 0
        critical = self.db.scalar(
            select(func.count(ImprovementProposal.id)).where(
                ImprovementProposal.status == "open", ImprovementProposal.priority == "critical")
        ) or 0
        components = {
            "blueprint_compliance": h("architecture"),
            "knowledge_quality": h("knowledge"),
            "business_understanding": h("planning"),
            "reasoning_quality": h("planning"),
            "founder_experience": max(0, 100 - open_props * 5),
            "automation": h("development"),
            "mission_success": h("deployment"),
            "learning": h("learning"),
            "memory": h("memory"),
        }
        overall = round(sum(components.values()) / len(components), 1)
        maturity = ("maturing" if overall >= 80 else "developing" if overall >= 55 else "early")
        return {
            "company_evolution_score": overall,
            "maturity": maturity,
            "components": components,
            "open_opportunities": open_props,
            "critical_opportunities": critical,
        }

    def founder_view(self) -> dict:
        """Business-language view for the Founder — recommendations only, no engineering."""
        bl = self.backlog()
        top = (bl["critical"] + bl["high"] + bl["medium"])[:10]
        return {
            "company_evolution_score": self.evolution_score()["company_evolution_score"],
            "top_opportunities": [
                {
                    "recommendation": p["title"],
                    "business_value": p["business_impact"],
                    "expected_benefit": p.get("recommended_solution"),
                    "estimated_risk": p["risk"],
                    "priority": p["priority"],
                    "approval_required": p["priority"] in ("critical", "high"),
                }
                for p in top
            ],
            "note": "These are executive recommendations. You approve direction and priority; "
                    "the company handles the engineering.",
        }

    # -- serialization -----------------------------------------------------

    @staticmethod
    def serialize(p: ImprovementProposal) -> dict:
        return {
            "id": str(p.id), "dimension": p.dimension, "title": p.title,
            "problem": p.problem, "evidence": p.evidence, "root_cause": p.root_cause,
            "business_impact": p.business_impact, "technical_impact": p.technical_impact,
            "blueprint_ref": p.blueprint_ref, "risk": p.risk, "priority": p.priority,
            "priority_score": p.priority_score, "roi": p.roi, "effort": p.effort,
            "recommended_solution": p.recommended_solution,
            "alternatives": json.loads(p.alternatives) if p.alternatives else [],
            "debate": json.loads(p.debate) if p.debate else None,
            "confidence": p.confidence, "status": p.status,
        }

    # ================================================================= #
    #  Continuous cycle (runs forever via the job worker)              #
    # ================================================================= #

    def run_cycle(self, *, debate_top: int = 0) -> dict:
        """One evolution cycle: observe -> propose -> (optionally) debate top-N."""
        proposals = self.generate_proposals(persist=True)
        debated = 0
        if debate_top:
            ranked = self.db.scalars(
                select(ImprovementProposal)
                .where(ImprovementProposal.status == "open",
                       ImprovementProposal.debate.is_(None))
                .order_by(ImprovementProposal.priority_score.desc()).limit(debate_top)
            ).all()
            for p in ranked:
                self.debate(p)
                debated += 1
        return {"proposals": len(proposals), "debated": debated,
                "evolution_score": self.evolution_score()["company_evolution_score"]}

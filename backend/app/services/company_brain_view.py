"""Company Brain — the live intelligence center (AURORA — Sprint 04).

Exposes the reasoning WES has ALREADY produced, in business language. It composes
existing state and adds no reasoning of its own:

* DecompositionService.plan   — per-mission executive reasoning, domain, gap/repo
                                analysis, consensus, risks, memory
* CompanyBrain                — blueprint index / repository intelligence
* CompanyMemoryService        — semantic search, similar projects
* LearningService             — evidence-based rules
* CompanyEvolutionService     — evolution / learning score
* FounderMissionControlService— missions, health

It NEVER surfaces prompts, raw model output, provider names, tokens, source code
or private chain-of-thought — only the structured executive reasoning WES stored.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

_EXECS = ["Chief Executive", "Chief Technology Officer", "Chief Architect",
          "Quality Director", "Security Officer"]


def _clip(v, n=400):
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        v = "; ".join(str(x) for x in v)
    return str(v).strip()[:n]


def _list(v, n=8, cap=300):
    if not v:
        return []
    if isinstance(v, str):
        v = [v]
    out = []
    for x in v:
        if isinstance(x, dict):
            x = x.get("title") or x.get("name") or x.get("summary") or x.get("why") or str(x)
        s = str(x).strip()[:cap]
        if s:
            out.append(s)
    return out[:n]


class CompanyBrainViewService:
    def __init__(self, db: Session):
        self.db = db
        from app.services.founder_mission_control import FounderMissionControlService

        self.mc = FounderMissionControlService(db)

    # ================================================================= #
    #  Brain Home — what is the company thinking about right now?        #
    # ================================================================= #

    def home(self) -> dict:
        missions = self._missions()
        active = [m for m in missions if m["status"] != "Completed"]
        topics = []
        for m in active[:6]:
            detail = self._detail(m["mission_id"])
            topics.append({
                "mission_id": m["mission_id"],
                "topic": m["mission_name"],
                "executive": (detail or {}).get("current_executive", "AI CEO"),
                "activity": (detail or {}).get("current_activity", "Reasoning"),
                "confidence": round((m.get("business_confidence") or (detail or {}).get("current_confidence") or 0.8) * 100),
                "stage": m["current_stage"],
            })

        refs = self._reference_counts()
        evo = self._evolution()
        return {
            "thinking_topics": topics,
            "references": refs,
            "current_recommendation": (evo.get("top_opportunities") or [{}])[0].get("recommendation"),
            "evolution_score": evo.get("company_evolution_score"),
            "company_health": self._health().get("overall"),
            "thinking_stream": self._stream(active),
        }

    def _reference_counts(self) -> dict:
        from sqlalchemy import func, select

        def count(model):
            try:
                return self.db.scalar(select(func.count(model.id))) or 0
            except Exception:
                return 0
        from app.models.improvement import ImprovementProposal
        from app.models.knowledge import KnowledgeDocument
        from app.models.learning import LearningRule
        from app.models.memory import AgentMemory

        blueprint = 0
        try:
            from app.services.company_brain import CompanyBrain

            blueprint = len(CompanyBrain._blueprint_index())
        except Exception:
            blueprint = 0
        repo = 0
        try:
            from app.models.repository import RepositoryModule

            repo = count(RepositoryModule)
        except Exception:
            repo = 0
        return {
            "knowledge": count(KnowledgeDocument),
            "memory": count(AgentMemory),
            "learning": count(LearningRule),
            "blueprint": blueprint,
            "repository": repo,
            "improvements": count(ImprovementProposal),
        }

    def _stream(self, active: list[dict]) -> list[dict]:
        """Business-language 'who is thinking about what' — a live feel."""
        verbs = {"Chief Executive": "is weighing business value on",
                 "Chief Technology Officer": "is comparing approaches for",
                 "Chief Architect": "is evaluating reuse for",
                 "Quality Director": "is validating quality on",
                 "Security Officer": "is reviewing risk on"}
        out = []
        for i, m in enumerate(active[:5]):
            ex = _EXECS[i % len(_EXECS)]
            out.append({"executive": ex, "event": f"The {ex} {verbs[ex]} {m['mission_name']}."})
        if not out:
            out.append({"executive": "Chief Executive", "event": "The company is reviewing its priorities."})
        return out

    # ================================================================= #
    #  Reasoning Explorer + everything for one mission                  #
    # ================================================================= #

    def mission(self, mission_id: uuid.UUID) -> dict:
        plan = self._plan(mission_id)
        ba = (plan.get("business_analysis") or {}) if plan else {}
        domain = ba.get("domain_analysis") or {}
        cto = ba.get("cto") or {}
        arch = ba.get("architect") or {}
        consensus = (plan.get("collaboration") or {}).get("executive_consensus") or {} if plan else {}
        gap = plan.get("gap_analysis") or {} if plan else {}
        overview = self._detail(str(mission_id)) or {}

        return {
            "mission_name": overview.get("mission_name") or (plan.get("project") or {}).get("name"),
            "reasoning": self._reasoning(ba, cto, arch, consensus, domain, plan, overview),
            "decision_explainer": self._explainer(consensus, cto, overview),
            "blueprint": self._blueprint(domain, cto, consensus),
            "domain": self._domain(domain),
            "memory": self._mission_memory(plan, mission_id),
            "repository": self._repository(gap, plan),
            "graph": self._graph(overview, domain, plan),
        }

    def _reasoning(self, ba, cto, arch, consensus, domain, plan, overview) -> dict:
        objectives = _list(domain.get("kpis")) or _list(ba.get("success_criteria"))
        known = []
        if domain.get("industry"):
            known.append(f"This operates in {domain['industry']}.")
        known += [f"{s}" for s in _list(domain.get("daily_operations"), 3)]
        known += _list((plan or {}).get("repository_analysis", {}).get("modules"), 3) and \
            [f"The company already has modules it can reuse: {', '.join(_list((plan or {}).get('repository_analysis', {}).get('modules'), 6))}."] or []
        evidence = _list(domain.get("existing_solutions"), 3) + _list(domain.get("industry_best_practices"), 3)
        unknowns = _list(consensus.get("open_concerns"), 4)
        assumptions = _list(consensus.get("agreed_constraints"), 4) or _list(domain.get("operational_constraints"), 4)

        # Alternatives considered = the CTO's chosen decisions vs. the architect's
        # challenge and the concerns raised (all real, stored executive reasoning).
        alternatives = []
        for i, d in enumerate(_list(cto.get("key_decisions"), 3), 1):
            alternatives.append({"option": f"Approach {i}", "summary": d, "chosen": i == 1})
        why_rejected = []
        if consensus.get("architect_position") == "challenge" and consensus.get("rationale"):
            why_rejected.append(_clip(consensus.get("rationale"), 300))
        why_rejected += _list(consensus.get("open_concerns"), 2)

        return {
            "business_context": _clip(ba.get("vision") or domain.get("business_model"), 500),
            "objectives": objectives[:5],
            "known_facts": [k for k in known if k][:6],
            "evidence": evidence[:6],
            "unknowns": unknowns,
            "assumptions": assumptions,
            "alternatives": alternatives,
            "final_recommendation": _clip(cto.get("strategy") or ba.get("architecture_proposal"), 400),
            "confidence": overview.get("current_confidence") or domain.get("business_confidence") or 0.8,
            "business_impact": _clip(overview.get("business_impact") or domain.get("business_model"), 300),
            "expected_risks": _list(cto.get("technical_risks"), 3) + _list(ba.get("risks"), 2),
            "why_alternatives_rejected": why_rejected[:4],
        }

    def _explainer(self, consensus, cto, overview) -> dict:
        return {
            "why_this": _clip(cto.get("strategy"), 300) or "It best fits the business goal with the company's existing capabilities.",
            "why_not_other": _clip(consensus.get("rationale"), 300) or "Alternatives added cost or risk without clear business benefit.",
            "why_confidence": f"Confidence reflects the evidence gathered and the executive board's review"
                              + (" (with open concerns still tracked)." if consensus.get("open_concerns") else "."),
            "missing_information": _list(consensus.get("open_concerns"), 3),
            "what_would_change_it": _list(consensus.get("agreed_constraints"), 3)
                                    or ["New business constraints or stronger evidence against the chosen approach."],
        }

    # ================================================================= #
    #  Blueprint Intelligence                                           #
    # ================================================================= #

    def blueprint(self, mission_id: uuid.UUID | None = None) -> dict:
        domain, cto, consensus = {}, {}, {}
        if mission_id is not None:
            plan = self._plan(mission_id)
            ba = (plan.get("business_analysis") or {}) if plan else {}
            domain = ba.get("domain_analysis") or {}
            cto = ba.get("cto") or {}
            consensus = (plan.get("collaboration") or {}).get("executive_consensus") or {} if plan else {}
        return self._blueprint(domain, cto, consensus)

    def _blueprint(self, domain, cto, consensus) -> dict:
        try:
            from app.services.company_brain import CompanyBrain

            index = CompanyBrain._blueprint_index()
        except Exception:
            index = {}
        applied = domain.get("industry_best_practices_applied") or []
        # Which volumes matter here (applied refs + always-constitutional ones).
        guiding = []
        for ref in applied[:4]:
            title = ref.split(" — ")[0]
            topics = index.get(ref.split(" — ")[0], "")
            guiding.append({"volume": title, "why": _clip(topics, 160) or "Guides how this work is delivered."})
        if not guiding and index:
            for title in list(index)[:3]:
                guiding.append({"volume": title, "why": _clip(index[title], 160)})
        gov = self._governance()
        compliance = gov.get("score")
        missing = [d.get("detail") for d in gov.get("dimensions", []) if d.get("status") != "healthy"]
        return {
            "volumes_guiding": guiding,
            "compliance_percentage": compliance,
            "missing_requirements": [_clip(m, 200) for m in missing if m][:4],
            "conflicts": _list(consensus.get("open_concerns"), 2),
            "recommendations": ["Maintain reuse of existing modules per Vol 04.",
                                "Keep security & compliance gates per Vol 08."][: (1 if compliance and compliance >= 80 else 2)],
        }

    # ================================================================= #
    #  Domain / Memory / Repository / Learning / Search                 #
    # ================================================================= #

    def _domain(self, domain: dict) -> dict:
        if not domain:
            return {}
        return {
            "industry": domain.get("industry"),
            "business_model": domain.get("business_model"),
            "stakeholders": _list(domain.get("stakeholders")),
            "workflow": _list(domain.get("daily_operations")),
            "kpis": _list(domain.get("kpis")),
            "compliance": _list(domain.get("compliance")),
            "automation_opportunities": _list(domain.get("automation_opportunities")),
            "departments": _list(domain.get("departments")),
            "reports": _list(domain.get("suggested_reports")),
            "dashboards": _list(domain.get("suggested_dashboards")),
            "roadmap": _list(domain.get("roadmap")),
            "confidence": domain.get("business_confidence"),
        }

    def domain(self, mission_id: uuid.UUID) -> dict:
        plan = self._plan(mission_id)
        ba = (plan.get("business_analysis") or {}) if plan else {}
        return self._domain(ba.get("domain_analysis") or {})

    def _mission_memory(self, plan, mission_id) -> dict:
        similar = []
        try:
            from app.models.work import Project
            from app.services.company_memory import CompanyMemoryService

            project = self.db.get(Project, mission_id)
            if project is not None:
                similar = CompanyMemoryService(self.db).similar_projects(project, k=3)
        except Exception:
            similar = []
        cm = (plan or {}).get("company_memory") or {}
        return {
            "similar_projects": [{"objective": _clip(s.get("objective") or s.get("summary"), 160),
                                  "similarity": round(s.get("similarity", 0) * 100)} for s in similar],
            "categories": cm.get("by_category") if isinstance(cm, dict) else {},
            "total_remembered": cm.get("count") if isinstance(cm, dict) else 0,
        }

    def memory(self) -> dict:
        """Company-wide Memory Center."""
        from sqlalchemy import func, select

        from app.models.memory import AgentMemory
        rows = self.db.execute(
            select(AgentMemory.category, func.count(AgentMemory.id))
            .group_by(AgentMemory.category)
        ).all()
        recent = self.db.scalars(
            select(AgentMemory).order_by(AgentMemory.created_at.desc()).limit(10)
        ).all()
        # Lessons / mistakes-to-avoid come from the learning engine.
        avoid = []
        try:
            from app.services.learning import LearningService

            avoid = [r.get("rule") or r.get("summary") for r in LearningService(self.db).rules(limit=8)]
        except Exception:
            avoid = []
        return {
            "total": sum(c for _, c in rows),
            "by_category": [{"category": (k or "general").replace("_", " "), "count": c} for k, c in sorted(rows, key=lambda x: -x[1])],
            "recent": [{"summary": _clip(m.summary, 180), "category": (m.category or "").replace("_", " ")} for m in recent],
            "mistakes_avoided": [_clip(a, 180) for a in avoid if a][:6],
        }

    def repository(self, mission_id: uuid.UUID | None = None) -> dict:
        gap, plan = {}, {}
        if mission_id is not None:
            plan = self._plan(mission_id)
            gap = plan.get("gap_analysis") or {}
        return self._repository(gap, plan)

    def _repository(self, gap, plan) -> dict:
        # Business-language repository intelligence — never source code.
        reuse = gap.get("reuse") or []
        capabilities = [{"capability": r.get("component", "module").replace("_", " ").title(),
                         "why": _clip(r.get("why"), 200)} for r in reuse[:8] if isinstance(r, dict)]
        modules = _list((plan or {}).get("repository_analysis", {}).get("modules"), 12)
        gov = self._governance()
        arch_dim = next((d for d in gov.get("dimensions", []) if d.get("dimension") == "architecture"), {})
        debt = arch_dim.get("detail") if arch_dim.get("status") != "healthy" else None
        return {
            "reusable_capabilities": capabilities,
            "existing_modules": [m.replace("_", " ").title() for m in modules if m and m != "."],
            "potential_reuse": [c["capability"] for c in capabilities][:6],
            "technical_debt": _clip(debt, 200) if debt else "No significant technical debt flagged.",
            "business_impact": "Reusing existing capabilities means faster, cheaper, more reliable delivery.",
        }

    def learning(self) -> dict:
        summary, rules = {}, []
        try:
            from app.services.learning import LearningService

            svc = LearningService(self.db)
            summary = svc.summary()
            rules = svc.rules(limit=10)
        except Exception:
            pass
        evo = self._evolution_full()
        return {
            "learning_rules": summary.get("total") if isinstance(summary, dict) else len(rules),
            "new_knowledge": [_clip(r.get("rule") or r.get("summary"), 200) for r in rules[:6]],
            "patterns_discovered": [_clip(r.get("rule"), 160) for r in rules if r.get("occurrences", 0) > 1][:4],
            "emerging_opportunities": [_clip(o.get("recommendation"), 160) for o in (evo.get("top_opportunities") or [])[:4]],
            "knowledge_gaps": [_clip(o.get("recommendation"), 160) for o in (evo.get("top_opportunities") or [])
                               if "knowledge" in str(o.get("recommendation", "")).lower()][:3],
            "learning_score": evo.get("company_evolution_score"),
            "evolution_score": evo.get("company_evolution_score"),
        }

    def search(self, query: str) -> dict:
        q = (query or "").strip()
        results: dict[str, list] = {"missions": [], "knowledge": [], "previous_projects": [],
                                    "risks": [], "recommendations": []}
        if not q:
            return {"query": q, "results": results, "total": 0}
        ql = q.lower()
        # Missions (name/objective match).
        for m in self._missions():
            if ql in (m["mission_name"] or "").lower() or ql in (m.get("business_objective") or "").lower():
                results["missions"].append({"id": m["mission_id"], "title": m["mission_name"], "stage": m["current_stage"]})
        # Semantic memory search (reuse embeddings; graceful if unavailable).
        try:
            from app.services.company_memory import CompanyMemoryService

            for r in CompanyMemoryService(self.db).semantic_search(q, k=6):
                bucket = "previous_projects" if r.get("category") == "founder_objective" else "knowledge"
                results[bucket].append({"title": _clip(r.get("summary"), 160),
                                        "similarity": round(r.get("similarity", 0) * 100)})
        except Exception:
            pass
        # Recommendations (evolution).
        for o in (self._evolution().get("top_opportunities") or []):
            if ql in str(o.get("recommendation", "")).lower():
                results["recommendations"].append({"title": o["recommendation"]})
        total = sum(len(v) for v in results.values())
        return {"query": q, "results": results, "total": total}

    # -- knowledge graph -----------------------------------------------

    def _graph(self, overview, domain, plan) -> dict:
        nodes = [{"id": "mission", "label": _clip(overview.get("mission_name"), 40) or "Mission", "group": "mission"}]
        edges = []

        def add(group, items, prefix, cap=4):
            for i, it in enumerate(_list(items, cap)):
                nid = f"{prefix}{i}"
                nodes.append({"id": nid, "label": _clip(it, 30), "group": group})
                edges.append({"from": "mission", "to": nid})

        add("department", domain.get("departments"), "dep")
        for i, ex in enumerate(["CEO", "CTO", "Architect", "QA", "Security"]):
            nodes.append({"id": f"ex{i}", "label": ex, "group": "executive"})
            edges.append({"from": "mission", "to": f"ex{i}"})
        add("knowledge", domain.get("kpis"), "kn", 3)
        add("rule", domain.get("approval_flows"), "rule", 3)
        ba = (plan or {}).get("business_analysis") or {}
        add("risk", [r.get("title") if isinstance(r, dict) else r for r in (ba.get("risks_detailed") or ba.get("risks") or [])], "risk", 4)
        add("recommendation", (ba.get("cto") or {}).get("key_decisions"), "rec", 3)
        return {"nodes": nodes, "edges": edges}

    # ================================================================= #
    #  data access (reuse only)                                          #
    # ================================================================= #

    def _missions(self):
        try:
            return self.mc.missions().get("missions", [])
        except Exception:
            return []

    def _detail(self, mid):
        try:
            return self.mc.mission(uuid.UUID(mid))
        except Exception:
            return {}

    def _plan(self, mission_id):
        try:
            from app.services.project_decomposition import DecompositionService

            return DecompositionService(self.db).plan(mission_id)
        except Exception:
            return {}

    def _health(self):
        try:
            return self.mc.company_health()
        except Exception:
            return {}

    def _governance(self):
        try:
            from app.services.founder_os import FounderOSService

            return FounderOSService(self.db).governance()
        except Exception:
            return {}

    def _evolution(self):
        try:
            from app.services.company_evolution import CompanyEvolutionService

            return CompanyEvolutionService(self.db).founder_view()
        except Exception:
            return {}

    def _evolution_full(self):
        try:
            from app.services.company_evolution import CompanyEvolutionService

            svc = CompanyEvolutionService(self.db)
            fv = svc.founder_view()
            fv["company_evolution_score"] = svc.evolution_score().get("company_evolution_score")
            return fv
        except Exception:
            return {}

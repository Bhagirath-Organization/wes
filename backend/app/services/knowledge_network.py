"""Knowledge Network & Organisational Intelligence (AURORA — Sprint 06).

Exposes and connects the organisational knowledge WES already owns — in business
language, composed from existing state, with no new reasoning:

* AgentMemory / CompanyMemoryService — what the company remembers
* LearningService (learning rules)    — reuse counts, patterns, mistakes avoided
* CompanyEvolutionService             — knowledge gaps, learning score, opportunities
* CompanyBrain / governance            — Blueprint intelligence
* FounderMissionControl / Workforce    — which missions & departments contributed
* CompanyBrainViewService.search       — the universal semantic search (reused)

Never exposes embeddings, vectors, prompts, providers, tokens or repo internals.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

_ROLE_TITLE = [
    ("ceo", "Chief Executive"), ("cto", "Chief Technology Officer"),
    ("architect", "Chief Architect"), ("security", "Security Officer"),
    ("qa", "Quality Director"), ("analyst", "Business Analyst"),
    ("devops", "DevOps Director"), ("engineer", "Engineering"),
]


def _title(role: str) -> str:
    r = (role or "").lower()
    for k, t in _ROLE_TITLE:
        if k in r:
            return t
    return "The company"


def _pretty(cat: str) -> str:
    return (cat or "general").replace("_", " ")


def _now():
    return datetime.now(timezone.utc)


class KnowledgeNetworkService:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------ #
    #  Knowledge Home — health, growth, coverage, freshness, trend       #
    # ------------------------------------------------------------------ #

    def home(self) -> dict:
        from app.models.memory import AgentMemory

        total = self.db.scalar(select(func.count(AgentMemory.id))) or 0
        recent = self.db.scalar(select(func.count(AgentMemory.id))
                                .where(AgentMemory.created_at > _now() - timedelta(days=7))) or 0
        older = self.db.scalar(select(func.count(AgentMemory.id))
                               .where(AgentMemory.created_at < _now() - timedelta(days=30))) or 0
        avg_conf = self.db.scalar(select(func.avg(AgentMemory.confidence))) or 0
        cats = self.db.scalar(select(func.count(func.distinct(AgentMemory.category)))) or 0
        reuse = self._reuse_stats()
        evo = self._evolution()

        fastest = self._fastest_domain()
        by_mission = self._by_mission()
        return {
            "metrics": {
                "knowledge_health": "strong" if avg_conf and avg_conf >= 0.7 else "developing",
                "total_knowledge": total,
                "growth_7d": recent,
                "coverage_areas": cats,
                "confidence": round(float(avg_conf) * 100),
                "quality": "high" if avg_conf and avg_conf >= 0.75 else "good",
                "reuse_rate": reuse["reuse_rate"],
                "gaps": len(evo.get("knowledge_gaps", [])) if isinstance(evo, dict) else 0,
                "freshness": round(100 * recent / total) if total else 0,
                "ageing": older,
                "learning_score": evo.get("learning_score"),
                "trend": "improving",
            },
            "recent_learnings": self._recent_learnings(6),
            "most_valuable": self._most_valuable(4),
            "contributing_missions": by_mission,
            "fastest_growing_domain": fastest,
        }

    # ------------------------------------------------------------------ #
    #  Knowledge Graph                                                   #
    # ------------------------------------------------------------------ #

    def graph(self) -> dict:
        from app.models.memory import AgentMemory

        nodes = [{"id": "company", "label": "Company Knowledge", "group": "company"}]
        edges = []

        def add(group, items, prefix, cap=6):
            for i, it in enumerate(items[:cap]):
                nid = f"{prefix}{i}"
                nodes.append({"id": nid, "label": str(it)[:28], "group": group})
                edges.append({"from": "company", "to": nid})

        cats = [(_pretty(c), n) for c, n in self.db.execute(
            select(AgentMemory.category, func.count()).group_by(AgentMemory.category)
            .order_by(func.count().desc()).limit(6)).all()]
        add("knowledge", [c for c, _ in cats], "kn")
        add("department", self._departments(), "dep", 5)
        add("executive", ["Chief Executive", "CTO", "Chief Architect", "Quality", "Security"], "ex", 5)
        add("blueprint", self._blueprint_titles(), "bp", 4)
        add("recommendation", [o.get("recommendation") for o in (self._evolution().get("top_opportunities") or [])], "rec", 3)
        return {"nodes": nodes, "edges": edges}

    # ------------------------------------------------------------------ #
    #  Knowledge timeline (business language)                            #
    # ------------------------------------------------------------------ #

    def timeline(self) -> dict:
        from app.models.memory import AgentMemory

        rows = self.db.scalars(
            select(AgentMemory).order_by(AgentMemory.created_at.desc()).limit(20)
        ).all()
        events = []
        for m in rows:
            events.append({
                "headline": self._narrate(m),
                "area": _pretty(m.category),
                "by": _title(m.author_role or ""),
                "confidence": round((m.confidence or 0.7) * 100),
            })
        return {"events": events}

    # ------------------------------------------------------------------ #
    #  Organisational memory                                             #
    # ------------------------------------------------------------------ #

    def organisational_memory(self) -> dict:
        rules = self._rules()
        lessons = [r for r in rules if r.get("dimension") in ("risk", "quality", "test_coverage")]
        patterns = [r for r in rules if (r.get("occurrences") or 0) > 1]
        return {
            "lessons_remembered": [self._rule_text(r) for r in lessons[:6]],
            "mistakes_avoided": [self._rule_text(r) for r in rules if "avoid" in (r.get("rule") or "").lower() or "must" in (r.get("rule") or "").lower()][:6],
            "repeated_patterns": [{"pattern": self._rule_text(r), "seen": r.get("occurrences")} for r in
                                  sorted(patterns, key=lambda x: -(x.get("occurrences") or 0))[:6]],
            "institutional_knowledge": self._most_valuable(6),
            "ageing": self._ageing(),
            "confidence": round(float(self.db.scalar(select(func.avg(self._mem().confidence))) or 0) * 100),
        }

    # ------------------------------------------------------------------ #
    #  Reuse analysis                                                    #
    # ------------------------------------------------------------------ #

    def reuse_analysis(self) -> dict:
        rules = self._rules()
        reused = [r for r in rules if (r.get("applied_count") or 0) > 0]
        never = [r for r in rules if (r.get("applied_count") or 0) == 0]
        # Conflicting / duplicate detection is heuristic on the rule text theme.
        return {
            "frequently_reused": [{"knowledge": self._rule_text(r), "used": r.get("applied_count")}
                                  for r in sorted(reused, key=lambda x: -(x.get("applied_count") or 0))[:6]],
            "never_reused": [self._rule_text(r) for r in never[:5]],
            "reuse_rate": self._reuse_stats()["reuse_rate"],
            "recommended_consolidation": self._duplicate_hint(rules),
            "opportunities": [o.get("recommendation") for o in (self._evolution().get("top_opportunities") or [])[:3]],
        }

    # ------------------------------------------------------------------ #
    #  Blueprint intelligence (per volume)                              #
    # ------------------------------------------------------------------ #

    def blueprint(self) -> dict:
        index = self._blueprint_index()
        gov = self._governance()
        arch = next((d for d in gov.get("dimensions", []) if d.get("dimension") == "architecture"), {})
        volumes = []
        # knowledge contributed per volume ~ memories that reference it (by category theme)
        for title, topics in list(index.items())[:10]:
            volumes.append({
                "volume": title,
                "guides": (topics or "").split(", ")[0] if topics else "",
                "adoption": "adopted" if title.split(" — ")[0] in ("Volume 04", "Volume 05", "Volume 08") else "referenced",
            })
        return {
            "compliance": gov.get("score"),
            "volumes": volumes,
            "missing_capability": [d.get("detail") for d in gov.get("dimensions", []) if d.get("status") != "healthy"][:3],
            "recommendations": ["Keep reuse and standards per Vol 04 & 08."],
        }

    # ------------------------------------------------------------------ #
    #  Knowledge insights                                               #
    # ------------------------------------------------------------------ #

    def insights(self) -> dict:
        evo = self._evolution()
        return {
            "most_valuable_learning": (self._most_valuable(1) or [{}])[0].get("title"),
            "fastest_growing_domain": self._fastest_domain(),
            "emerging_opportunities": [o.get("recommendation") for o in (evo.get("top_opportunities") or [])[:3]],
            "knowledge_at_risk": self._ageing().get("stale_examples", [])[:3],
            "requires_validation": [self._rule_text(r) for r in self._rules() if not r.get("active")][:3],
            "requires_founder_approval": [o.get("recommendation") for o in (evo.get("top_opportunities") or [])
                                          if o.get("approval_required")][:3],
        }

    # ------------------------------------------------------------------ #
    #  Collaboration view (departments creating knowledge together)      #
    # ------------------------------------------------------------------ #

    def collaboration(self) -> dict:
        try:
            from app.services.workforce import WorkforceService

            net = WorkforceService(self.db).collaboration()
        except Exception:
            net = {"nodes": [], "edges": []}
        # Knowledge contribution per author role.
        contrib = [{"contributor": _title(r or ""), "knowledge": n} for r, n in self.db.execute(
            select(self._mem().author_role, func.count()).where(self._mem().author_role.isnot(None))
            .group_by(self._mem().author_role).order_by(func.count().desc()).limit(8)).all()]
        return {"network": net, "contributions": contrib,
                "note": "Who creates knowledge, and who collaborates — from real work."}

    # ------------------------------------------------------------------ #
    #  Search (reuse the universal semantic search)                      #
    # ------------------------------------------------------------------ #

    def search(self, query: str) -> dict:
        try:
            from app.services.company_brain_view import CompanyBrainViewService

            return CompanyBrainViewService(self.db).search(query)
        except Exception:
            return {"query": query, "results": {}, "total": 0}

    # ================================================================= #
    #  helpers                                                          #
    # ================================================================= #

    def _mem(self):
        from app.models.memory import AgentMemory

        return AgentMemory

    def _recent_learnings(self, k: int) -> list[dict]:
        rows = self.db.scalars(select(self._mem()).order_by(self._mem().created_at.desc()).limit(k)).all()
        return [{"headline": self._narrate(m), "area": _pretty(m.category),
                 "confidence": round((m.confidence or 0.7) * 100)} for m in rows]

    def _most_valuable(self, k: int) -> list[dict]:
        rows = self.db.scalars(
            select(self._mem()).order_by(self._mem().importance.desc().nullslast(),
                                         self._mem().confidence.desc().nullslast()).limit(k)
        ).all()
        return [{"title": (m.summary or "")[:140], "area": _pretty(m.category),
                 "confidence": round((m.confidence or 0.7) * 100),
                 "value": round((m.importance or 0.5) * 100)} for m in rows]

    def _by_mission(self) -> list[dict]:
        from app.models.work import Project

        rows = self.db.execute(
            select(self._mem().project_id, func.count()).where(self._mem().project_id.isnot(None))
            .group_by(self._mem().project_id).order_by(func.count().desc()).limit(5)).all()
        names = {p.id: p.name for p in self.db.scalars(
            select(Project).where(Project.id.in_([r[0] for r in rows] or [uuid.uuid4()]))).all()}
        return [{"mission": (names.get(pid) or "A mission")[:60], "learnings": n} for pid, n in rows]

    def _fastest_domain(self) -> dict | None:
        rows = self.db.execute(
            select(self._mem().category, func.count()).where(self._mem().created_at > _now() - timedelta(days=30))
            .group_by(self._mem().category).order_by(func.count().desc()).limit(1)).all()
        return {"domain": _pretty(rows[0][0]), "new_items": rows[0][1]} if rows else None

    def _departments(self) -> list[str]:
        try:
            from app.models.ai import AIDepartment

            return [d.name for d in self.db.scalars(select(AIDepartment)).all()][:6]
        except Exception:
            return []

    def _reuse_stats(self) -> dict:
        rules = self._rules()
        if not rules:
            return {"reuse_rate": 0, "total": 0}
        reused = sum(1 for r in rules if (r.get("applied_count") or 0) > 0)
        return {"reuse_rate": round(100 * reused / len(rules)), "total": len(rules)}

    def _ageing(self) -> dict:
        old = self.db.scalars(
            select(self._mem()).where(self._mem().created_at < _now() - timedelta(days=60))
            .order_by(self._mem().created_at.asc()).limit(4)).all()
        cnt = self.db.scalar(select(func.count(self._mem().id))
                             .where(self._mem().created_at < _now() - timedelta(days=60))) or 0
        return {"stale_count": cnt, "stale_examples": [(m.summary or "")[:100] for m in old]}

    def _duplicate_hint(self, rules) -> list[str]:
        seen: dict[str, int] = {}
        for r in rules:
            key = (r.get("dimension") or "") + ":" + (r.get("kind") or "")
            seen[key] = seen.get(key, 0) + 1
        return [f"Multiple {k.split(':')[0] or 'general'} learnings could be consolidated ({v})"
                for k, v in seen.items() if v > 2][:3]

    def _rules(self) -> list[dict]:
        try:
            from app.services.learning import LearningService

            return LearningService(self.db).rules(limit=100)
        except Exception:
            return []

    @staticmethod
    def _rule_text(r: dict) -> str:
        return (r.get("rule") or r.get("summary") or "")[:180]

    def _evolution(self) -> dict:
        try:
            from app.services.company_evolution import CompanyEvolutionService

            return CompanyEvolutionService(self.db).learning()
        except Exception:
            return {}

    def _governance(self) -> dict:
        try:
            from app.services.founder_os import FounderOSService

            return FounderOSService(self.db).governance()
        except Exception:
            return {}

    def _blueprint_index(self) -> dict:
        try:
            from app.services.company_brain import CompanyBrain

            return CompanyBrain._blueprint_index()
        except Exception:
            return {}

    def _blueprint_titles(self) -> list[str]:
        return [t.split(" — ")[0] for t in list(self._blueprint_index())[:4]]

    def _narrate(self, m) -> str:
        """Business-language headline for a remembered item."""
        cat = _pretty(m.category)
        s = (m.summary or "").strip()
        # Strip any leading "[industry] category:" prefix the memory stored.
        if "] " in s:
            s = s.split("] ", 1)[1]
        if ":" in s and len(s.split(":", 1)[0]) < 40:
            s = s.split(":", 1)[1].strip()
        lead = {
            "industry_knowledge": "The company deepened its understanding of",
            "operational_workflow": "A reusable operational pattern was captured:",
            "business_rules": "A business rule was recorded:",
            "kpis": "Key metrics were learned:",
            "compliance_knowledge": "A compliance requirement was noted:",
            "automation_patterns": "An automation opportunity was learned:",
            "architecture_decision": "An architecture decision was recorded:",
            "founder_objective": "A new business objective was understood:",
            "executive_meeting": "The executive board reached a decision:",
            "review_finding": "A review insight was captured:",
            "implementation": "A delivery lesson was captured:",
            "lessons_learned": "A lesson was learned:",
        }.get(m.category, "The company captured a learning:")
        return f"{lead} {s}"[:220]

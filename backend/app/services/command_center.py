"""Founder Command Center & Business Intelligence (AURORA — Sprint 07).

The executive command room. It composes the organisational intelligence WES
already owns into decision support — no analytics engine, no new reasoning, no
duplicated logic. It reuses:

* FounderMissionControl / FounderOS  — missions, health, risks, decisions, governance
* CompanyEvolutionService            — opportunities, learning/evolution score
* KnowledgeNetworkService            — knowledge growth & reuse
* WorkforceService                   — utilisation & overload
* ExecutiveOfficeService             — the CEO's brief

Everything is business language. Providers, prompts, tokens, embeddings, repo
internals and engineering logs are never surfaced. Intentionally *light*: it uses
aggregate lists (not per-mission deep calls) so the command room loads instantly.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

# lifecycle stage -> owning executive (mirrors Mission Center; no heavy calls)
_STAGE_OWNER = {
    "Business Objective": "Chief Executive", "Business Understanding": "Business Analyst",
    "Executive Discussion": "Chief Executive", "Architecture": "Chief Architect",
    "Planning": "Chief Technology Officer", "Engineering": "Engineering Director",
    "Testing": "Quality Director", "Review": "Security Officer",
    "Deployment": "DevOps Director", "Business Validation": "Chief Executive",
    "Completed": "Chief Executive",
}
_EXECUTIVES = [
    ("Chief Executive", "Business value, priorities & growth", "planning"),
    ("Chief Technology Officer", "Technology strategy & scalability", "planning"),
    ("Chief Architect", "Architecture, reuse & technical debt", "architecture"),
    ("Engineering Director", "Delivery & implementation", "development"),
    ("Quality Director", "Quality, testing & release", "review"),
    ("Security Officer", "Risk, compliance & privacy", "review"),
    ("DevOps Director", "Deployment & availability", "deployment"),
]


def _pct(v):
    return None if v is None else round(float(v))


class CommandCenterService:
    def __init__(self, db: Session):
        self.db = db
        from app.services.founder_mission_control import FounderMissionControlService
        from app.services.founder_os import FounderOSService

        self.mc = FounderMissionControlService(db)
        self.founder = FounderOSService(db)

    # ------------------------------------------------------------------ #
    #  Executive overview (the headline KPIs)                            #
    # ------------------------------------------------------------------ #

    def overview(self) -> dict:
        missions = self._missions()
        active = [m for m in missions if m["status"] != "Completed"]
        done = [m for m in missions if m["status"] == "Completed"]
        health = self._health()
        decisions = self._decisions()
        evo = self._evolution()
        knowledge = self._knowledge()
        workforce = self._workforce_summary()
        risks = self._risks()

        avg_conf = self._avg_confidence(missions)
        avg_prog = round(sum(m["overall_progress"] for m in active) / len(active)) if active else 0

        return {
            "kpis": {
                "company_health": {"value": _pct(health.get("company_health_score")), "label": health.get("overall"), "trend": "stable"},
                "mission_health": {"value": avg_prog, "label": f"{len(active)} active", "trend": "up" if avg_prog else "flat"},
                "execution_velocity": {"value": len(done), "label": "delivered", "trend": "up" if done else "flat"},
                "decision_queue": {"value": len(decisions), "label": "need you", "trend": "up" if decisions else "clear"},
                "knowledge_growth": {"value": knowledge.get("growth_7d"), "label": "this week", "trend": "up"},
                "workforce_utilisation": {"value": workforce.get("utilisation"), "label": f"{workforce.get('working',0)}/{workforce.get('total',0)} engaged", "trend": "stable"},
                "executive_confidence": {"value": avg_conf, "label": "avg confidence", "trend": "stable"},
                "learning_trend": {"value": evo.get("company_evolution_score"), "label": "evolution", "trend": "up"},
                "business_risk": {"value": len(risks), "label": "tracked risks", "trend": "watch" if risks else "low"},
                "strategic_momentum": {"value": self._momentum(active, done, decisions), "label": "momentum", "trend": "up"},
            },
            "attention": self._attention(health, decisions, risks, workforce),
        }

    def _attention(self, health, decisions, risks, workforce) -> list[dict]:
        out = []
        if decisions:
            out.append({"kind": "decision", "text": f"{len(decisions)} decision{'s' if len(decisions)!=1 else ''} await your approval", "urgency": "high"})
        weak = [d for d in health.get("dimensions", []) if d.get("status") != "healthy"]
        for d in weak[:2]:
            out.append({"kind": "health", "text": f"{d['dimension'].replace('_',' ').title()} needs attention", "urgency": "medium"})
        if workforce.get("overloaded"):
            out.append({"kind": "workforce", "text": f"{len(workforce['overloaded'])} executive(s) carrying heavy load", "urgency": "medium"})
        if risks:
            out.append({"kind": "risk", "text": f"Top risk: {risks[0]['risk']}", "urgency": "medium"})
        return out[:5]

    # ------------------------------------------------------------------ #
    #  CEO daily brief                                                   #
    # ------------------------------------------------------------------ #

    def daily_brief(self, founder_name: str = "Founder") -> dict:
        from app.services.executive_office import ExecutiveOfficeService

        missions = self._missions()
        done = [m for m in missions if m["status"] == "Completed"]
        decisions = self._decisions()
        knowledge = self._knowledge()
        evo = self._evolution()

        yesterday = []
        if done:
            yesterday.append(f"{len(done)} mission{'s' if len(done)!=1 else ''} completed")
        if knowledge.get("growth_7d"):
            yesterday.append(f"{knowledge['growth_7d']} new knowledge assets")
        deployed = sum(1 for m in missions if m["current_stage"] in ("Deployment", "Business Validation"))
        if deployed:
            yesterday.append(f"{deployed} in deployment")

        priorities = []
        for d in decisions[:3]:
            priorities.append(d.get("title", "Review a decision"))
        for o in (evo.get("top_opportunities") or [])[:2]:
            if len(priorities) < 4:
                priorities.append(f"Consider: {o['recommendation']}")

        try:
            greeting = ExecutiveOfficeService(self.db).brief(founder_name)["greeting"]
        except Exception:
            greeting = f"Hello, {founder_name.split(' ')[0]}."
        return {
            "greeting": greeting,
            "yesterday": yesterday or ["A steady day across the company"],
            "today_priorities": priorities or ["Set a new business objective"],
            "closing": "Everything else is running autonomously.",
        }

    # ------------------------------------------------------------------ #
    #  Executive scoreboard                                              #
    # ------------------------------------------------------------------ #

    def scoreboard(self) -> dict:
        missions = self._missions()
        active = [m for m in missions if m["status"] != "Completed"]
        health = self._health()
        dims = {d.get("dimension"): d for d in health.get("dimensions", [])}
        decisions = self._decisions()

        board = []
        for title, responsibility, dim in _EXECUTIVES:
            owned = [m for m in active if _STAGE_OWNER.get(self._stage(m["current_stage"])) == title]
            dq = [d for d in decisions if self._decision_owner(d) == title]
            hstatus = (dims.get(dim, {}) or {}).get("status", "healthy")
            board.append({
                "executive": title, "responsibility": responsibility,
                "health": hstatus,
                "workload": len(owned),
                "confidence": self._avg_confidence(owned) or 80,
                "mission_ownership": [m["mission_name"] for m in owned][:3],
                "pending_decisions": len(dq),
                "business_impact": "Driving delivery" if owned else "Available",
                "trend": "up" if owned else "stable",
            })
        return {"executives": board}

    # ------------------------------------------------------------------ #
    #  Mission performance                                               #
    # ------------------------------------------------------------------ #

    def mission_performance(self) -> dict:
        try:
            from app.services.mission_center import MissionCenterService

            a = MissionCenterService(self.db).analytics()
        except Exception:
            a = {}
        missions = self._missions()
        active = [m for m in missions if m["status"] != "Completed"]
        blocked = [m for m in active if m["overall_progress"] < 15]
        return {
            "velocity": a.get("throughput", {}),
            "completion_rate": round(100 * a.get("throughput", {}).get("delivered", 0) / max(a.get("throughput", {}).get("total", 1), 1)),
            "blocked_missions": len(blocked),
            "executive_bottlenecks": a.get("executive_workload", [])[:3],
            "approval_latency": f"{len(self._decisions())} awaiting",
            "risk_trend": "stable",
            "business_value_delivered": a.get("business_value_delivered"),
            "forecast": self._forecast(active),
        }

    # ------------------------------------------------------------------ #
    #  Decision command (unified, enriched queue)                        #
    # ------------------------------------------------------------------ #

    def decision_command(self) -> dict:
        decisions = self._decisions()
        evo_reco = {o["recommendation"][:40]: o for o in (self._evolution().get("top_opportunities") or [])}
        items = []
        for d in decisions:
            items.append({
                "id": d.get("project_id"),
                "title": d.get("title"),
                "kind": d.get("kind"),
                "recommendation": d.get("why") or "The executive board recommends proceeding.",
                "business_impact": "Unblocks delivery of this mission.",
                "urgency": "high" if "deployment" in str(d.get("kind", "")) else "normal",
                "alternatives": ["Approve now", "Request changes", "Discuss with the board"],
                "expected_outcome": "The company proceeds to the next stage immediately.",
                "actions": ["Approve", "Review", "Discuss", "Delegate", "Schedule Later"],
            })
        return {"decisions": items, "total": len(items)}

    # ------------------------------------------------------------------ #
    #  Predictive insights (composed from real signals + confidence)     #
    # ------------------------------------------------------------------ #

    def predictions(self) -> dict:
        missions = self._missions()
        active = [m for m in missions if m["status"] != "Completed"]
        health = self._health()
        evo = self._evolution()
        workforce = self._workforce_summary()
        out = []

        early = [m for m in active if m["overall_progress"] < 40]
        if early:
            out.append({"prediction": f"{len(early)} mission(s) are early in their lifecycle and may take longer to deliver.",
                        "type": "delivery", "confidence": 70})
        arch = next((d for d in health.get("dimensions", []) if d.get("dimension") == "architecture"), {})
        if arch.get("status") != "healthy":
            out.append({"prediction": "Architecture health is below standard — technical risk will grow without attention.",
                        "type": "technical_risk", "confidence": 75})
        gaps = evo.get("knowledge_gaps") or []
        if gaps:
            out.append({"prediction": f"Knowledge gaps may slow future missions: {gaps[0]}.", "type": "knowledge", "confidence": 65})
        if workforce.get("overloaded"):
            out.append({"prediction": f"{len(workforce['overloaded'])} executive(s) are overloaded; delivery may bottleneck.",
                        "type": "resource", "confidence": 68})
        if self._decisions():
            out.append({"prediction": f"{len(self._decisions())} approval(s) are pending — the sooner decided, the faster the company moves.",
                        "type": "approvals", "confidence": 90})
        for o in (evo.get("top_opportunities") or [])[:2]:
            out.append({"prediction": f"Opportunity: {o['recommendation']}.", "type": "opportunity", "confidence": 72})
        return {"insights": out}

    # ------------------------------------------------------------------ #
    #  Company health (10 areas)                                         #
    # ------------------------------------------------------------------ #

    def company_health(self) -> dict:
        health = self._health()
        dims = {d.get("dimension"): d for d in health.get("dimensions", [])}

        def area(name, dim, owner):
            d = dims.get(dim, {})
            status = d.get("status", "healthy")
            return {"area": name, "health": status, "trend": "stable",
                    "confidence": 85 if status == "healthy" else 55, "owner": owner}
        areas = [
            area("Execution", "development", "Engineering Director"),
            area("Quality", "review", "Quality Director"),
            area("Knowledge", "knowledge", "Chief Executive"),
            area("Security", "review", "Security Officer"),
            area("Operations", "deployment", "DevOps Director"),
            area("Architecture", "architecture", "Chief Architect"),
            area("Business Alignment", "planning", "Chief Executive"),
            area("Innovation", "learning", "Chief Technology Officer"),
            area("Learning", "learning", "Chief Executive"),
            area("Compliance", "review", "Security Officer"),
        ]
        return {"overall": health.get("overall"), "score": _pct(health.get("company_health_score")), "areas": areas}

    # ------------------------------------------------------------------ #
    #  Business intelligence (executive KPIs)                            #
    # ------------------------------------------------------------------ #

    def business_intelligence(self) -> dict:
        k = self._knowledge()
        evo = self._evolution_full()
        wf = self._workforce_summary()
        missions = self._missions()
        active = [m for m in missions if m["status"] != "Completed"]
        done = [m for m in missions if m["status"] == "Completed"]
        return {
            "kpis": [
                {"kpi": "Delivery velocity", "value": len(done), "unit": "missions"},
                {"kpi": "Knowledge reuse", "value": k.get("reuse_rate"), "unit": "%"},
                {"kpi": "Learning velocity", "value": k.get("growth_7d"), "unit": "/week"},
                {"kpi": "Workforce utilisation", "value": wf.get("utilisation"), "unit": "%"},
                {"kpi": "Mission throughput", "value": len(missions), "unit": "total"},
                {"kpi": "Strategic alignment", "value": _pct(self._health().get("company_health_score")), "unit": "%"},
                {"kpi": "Evolution score", "value": evo.get("company_evolution_score"), "unit": "pts"},
                {"kpi": "Active missions", "value": len(active), "unit": "now"},
            ],
        }

    # ------------------------------------------------------------------ #
    #  Company timeline / Risk dashboard / Opportunity center            #
    # ------------------------------------------------------------------ #

    def timeline(self) -> dict:
        missions = self._missions()
        events = []
        for m in [x for x in missions if x["status"] == "Completed"][:4]:
            events.append({"headline": f"The company delivered {m['mission_name']}.", "kind": "delivery"})
        for m in [x for x in missions if x["status"] != "Completed"][:4]:
            events.append({"headline": f"{m['mission_name']} advanced to {m['current_stage'].lower()}.", "kind": "progress"})
        for o in (self._evolution().get("top_opportunities") or [])[:2]:
            events.append({"headline": f"The company recommended: {o['recommendation']}.", "kind": "insight"})
        return {"events": events[:10]}

    def risk_dashboard(self) -> dict:
        risks = self._risks()
        _OWN = {"Compliance": "Security Officer", "Technical": "Chief Architect",
                "Operational": "Engineering Director", "Business": "Chief Executive", "Financial": "Chief Executive"}
        out = []
        for r in risks:
            cat = r.get("category", "Business")
            out.append({"risk": r["risk"], "category": cat, "owner": _OWN.get(cat, "Chief Executive"),
                        "trend": "stable", "confidence": 70, "mitigation": "Tracked by the executive board."})
        return {"risks": out, "by_category": self._group(out)}

    def opportunity_center(self) -> dict:
        evo = self._evolution()
        k = self._knowledge()
        hiring = []
        try:
            from app.services.workforce import WorkforceService

            hiring = [r for r in WorkforceService(self.db).hiring_pipeline()["future_roles"] if r["status"] == "Recommended"]
        except Exception:
            hiring = []
        return {
            "high_value_improvements": [{"title": o["recommendation"], "value": o.get("business_value"), "approval": o.get("approval_required")}
                                        for o in (evo.get("top_opportunities") or [])[:5]],
            "fast_growing_domains": [k.get("fastest_growing_domain")] if k.get("fastest_growing_domain") else [],
            "reuse_rate": k.get("reuse_rate"),
            "future_hiring": [{"role": h["role"], "value": h["business_value"]} for h in hiring],
        }

    # ------------------------------------------------------------------ #
    #  Search (reuse universal semantic search)                          #
    # ------------------------------------------------------------------ #

    def search(self, query: str) -> dict:
        try:
            from app.services.company_brain_view import CompanyBrainViewService

            return CompanyBrainViewService(self.db).search(query)
        except Exception:
            return {"query": query, "results": {}, "total": 0}

    # ================================================================= #
    #  data access (all light aggregates)                               #
    # ================================================================= #

    def _missions(self):
        try:
            return self.mc.missions().get("missions", [])
        except Exception:
            return []

    def _health(self):
        try:
            return {**self.founder.governance(), **{k: v for k, v in self.mc.company_health().items() if k in ("overall", "company_health_score")}}
        except Exception:
            try:
                return self.founder.governance()
            except Exception:
                return {}

    def _decisions(self):
        try:
            return self.founder.decisions().get("items", [])
        except Exception:
            return []

    def _risks(self):
        try:
            return self.mc.risk_center().get("escalated_risks", [])
        except Exception:
            return []

    def _evolution(self):
        try:
            from app.services.company_evolution import CompanyEvolutionService

            fv = CompanyEvolutionService(self.db).founder_view()
            fv["company_evolution_score"] = fv.get("company_evolution_score")
            return fv
        except Exception:
            return {}

    def _evolution_full(self):
        try:
            from app.services.company_evolution import CompanyEvolutionService

            return CompanyEvolutionService(self.db).evolution_score()
        except Exception:
            return {}

    def _knowledge(self):
        try:
            from app.services.knowledge_network import KnowledgeNetworkService

            h = KnowledgeNetworkService(self.db).home()
            m = h.get("metrics", {})
            return {"growth_7d": m.get("growth_7d"), "reuse_rate": m.get("reuse_rate"),
                    "fastest_growing_domain": (h.get("fastest_growing_domain") or {}).get("domain")}
        except Exception:
            return {}

    def _workforce_summary(self):
        try:
            from app.services.workforce import WorkforceService

            s = WorkforceService(self.db).home()["summary"]
            util = round(100 * s["working"] / s["total"]) if s.get("total") else 0
            return {**s, "utilisation": util}
        except Exception:
            return {}

    def _avg_confidence(self, missions):
        c = [m.get("business_confidence") for m in missions if m.get("business_confidence")]
        return round(sum(c) / len(c) * 100) if c else None

    @staticmethod
    def _stage(lifecycle):
        from app.services.mission_center import _STAGE_MAP

        return _STAGE_MAP.get(lifecycle, "Understand Business")

    @staticmethod
    def _decision_owner(d):
        k = str(d.get("kind", ""))
        if "plan" in k:
            return "Chief Executive"
        if "pull_request" in k or "deployment" in k:
            return "DevOps Director"
        return "Chief Executive"

    @staticmethod
    def _momentum(active, done, decisions):
        base = 60 + min(len(done) * 3, 25) - min(len(decisions) * 2, 15)
        return max(0, min(100, base))

    @staticmethod
    def _forecast(active):
        if not active:
            return "No active missions."
        near = sum(1 for m in active if m["overall_progress"] >= 60)
        return f"{near} of {len(active)} active missions are on track to deliver soon."

    @staticmethod
    def _group(risks):
        g = {}
        for r in risks:
            g[r["category"]] = g.get(r["category"], 0) + 1
        return [{"category": k, "count": v} for k, v in sorted(g.items(), key=lambda x: -x[1])]

"""Mission Center + Living Company (AURORA — Sprint 03).

A business-language composition layer that lets the Founder *see the company
working*. It reuses everything and adds no business logic:

* FounderMissionControlService — missions, mission dashboard, health, risks, timeline
* DecompositionService.plan     — the already-stored executive discussion, domain
                                  understanding, risks, memory and blueprint context

Every field is composed from real stored state and translated into business
language. Task ids, branches, commits, providers and repository internals are
never surfaced.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

# The visible business lifecycle a mission moves through.
STAGES = [
    "Understand Business", "Executive Strategy", "Architecture", "Planning",
    "Engineering", "Quality", "Executive Review", "Founder Approval",
    "Deployment", "Business Validation", "Learning",
]
# Which lifecycle stage (from Mission Control) maps to which visible stage.
_STAGE_MAP = {
    "Business Objective": "Understand Business",
    "Business Understanding": "Understand Business",
    "Executive Discussion": "Executive Strategy",
    "Architecture": "Architecture",
    "Planning": "Planning",
    "Engineering": "Engineering",
    "Testing": "Quality",
    "Review": "Executive Review",
    "Deployment": "Deployment",
    "Business Validation": "Business Validation",
    "Completed": "Learning",
}

# The executive relay the Founder sees on the Mission Map.
MAP_ROLES = ["CEO", "CTO", "Chief Architect", "Engineering", "QA", "Security", "DevOps", "Founder"]
_STAGE_TO_ROLE = {
    "Understand Business": "CEO", "Executive Strategy": "CEO", "Architecture": "Chief Architect",
    "Planning": "CTO", "Engineering": "Engineering", "Quality": "QA",
    "Executive Review": "Security", "Founder Approval": "Founder", "Deployment": "DevOps",
    "Business Validation": "CEO", "Learning": "CEO",
}

# Executive display names for discussion turns.
_ROLE_TITLE = [
    ("ceo", "Chief Executive"), ("cto", "Chief Technology Officer"),
    ("architect", "Chief Architect"), ("security", "Security Officer"),
    ("qa", "Quality Director"), ("quality", "Quality Director"),
    ("devops", "DevOps Director"), ("backend", "Engineering Director"),
    ("frontend", "Engineering Director"), ("engineer", "Engineering Director"),
    ("product", "Product Lead"),
]


def _title_for(role: str) -> str:
    r = (role or "").lower()
    for key, title in _ROLE_TITLE:
        if key in r:
            return title
    return "Executive"


def _clip(v, n=400):
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        v = "; ".join(str(x) for x in v)
    return str(v).strip()[:n]


class MissionCenterService:
    def __init__(self, db: Session):
        self.db = db
        from app.services.founder_mission_control import FounderMissionControlService

        self.mc = FounderMissionControlService(db)

    # ================================================================= #
    #  Live Company — the company appears alive                          #
    # ================================================================= #

    def live_company(self) -> dict:
        missions = self._missions()
        active = [m for m in missions if m["status"] != "Completed"]
        health = self._health()
        executives: list[dict] = []
        seen = set()
        for m in active[:8]:
            detail = self._detail(m["mission_id"])
            ex = (detail or {}).get("current_executive", "AI CEO")
            executives.append({
                "executive": ex,
                "status": "working",
                "thinking": (detail or {}).get("current_activity", "Reviewing the mission"),
                "objective": m["mission_name"],
                "stage": self._stage(m["current_stage"]),
                "confidence": round((detail or {}).get("current_confidence", 0.8) * 100),
                "eta": (detail or {}).get("expected_completion", "In progress"),
            })
            seen.add(ex)
        # Idle executives stand ready (so the roster always feels complete).
        roster = ["AI CEO", "AI CTO", "AI Chief Architect", "AI Engineering Team",
                  "AI QA Lead", "AI Security Officer", "AI DevOps"]
        for r in roster:
            if r not in seen:
                executives.append({"executive": r, "status": "ready",
                                   "thinking": "Standing by", "objective": None,
                                   "stage": None, "confidence": None, "eta": None})
        return {
            "executives": executives,
            "active_missions": len(active),
            "company_health": health.get("overall"),
            "company_health_score": health.get("company_health_score"),
            "generated_at_stage": "live",
        }

    # ================================================================= #
    #  Mission detail — everything the Founder needs, business language  #
    # ================================================================= #

    def mission_detail(self, mission_id: uuid.UUID) -> dict:
        mid = str(mission_id)
        overview = self._detail(mid) or {}
        plan = self._plan(mission_id)
        ba = (plan.get("business_analysis") or {}) if plan else {}
        domain = ba.get("domain_analysis") or {}

        return {
            "overview": {
                "mission_name": overview.get("mission_name"),
                "business_goal": overview.get("business_objective"),
                "business_value": overview.get("business_value"),
                "business_stage": self._stage(overview.get("current_stage", "")),
                "current_executive": overview.get("current_executive"),
                "current_department": overview.get("current_department"),
                "current_activity": overview.get("current_activity"),
                "confidence": overview.get("current_confidence"),
                "progress": overview.get("overall_progress"),
                "health": "healthy" if not overview.get("current_blockers") else "attention",
                "expected_completion": overview.get("expected_completion"),
                "business_impact": overview.get("business_impact"),
                "deployment_status": overview.get("deployment_status"),
                "explanation": overview.get("explanation"),
            },
            "stages": self._stages(overview),
            "map": self._map(overview),
            "discussions": self._discussions(plan),
            "brain": self._brain(ba, domain, plan),
            "risks": self._risks(ba, domain),
            "decisions": self._decisions(overview, plan),
            "timeline": self._timeline(mid),
        }

    # -- stages / map ---------------------------------------------------

    def _stages(self, overview: dict) -> list[dict]:
        cur = self._stage(overview.get("current_stage", ""))
        try:
            idx = STAGES.index(cur)
        except ValueError:
            idx = 0
        return [{"stage": s, "state": "done" if i < idx else ("current" if i == idx else "upcoming")}
                for i, s in enumerate(STAGES)]

    def _map(self, overview: dict) -> dict:
        cur_stage = self._stage(overview.get("current_stage", ""))
        cur_role = _STAGE_TO_ROLE.get(cur_stage, "CEO")
        try:
            pos = MAP_ROLES.index(cur_role)
        except ValueError:
            pos = 0
        return {"roles": MAP_ROLES, "current": cur_role, "position": pos}

    # -- executive discussions (from stored, real conversation) --------

    def _discussions(self, plan: dict | None) -> list[dict]:
        if not plan:
            return []
        out: list[dict] = []
        for conv in (plan.get("conversations") or []):
            for msg in (conv.get("messages") or []):
                content = _clip(msg.get("content"), 500)
                if not content:
                    continue
                out.append({
                    "executive": _title_for(msg.get("from_role") or msg.get("from")),
                    "kind": msg.get("type") or "note",
                    "message": content,
                })
        # Add the plan review (Security + QA) as discussion, if present.
        review = (plan.get("collaboration") or {}).get("plan_review") or {}
        for r in (review.get("reviews") or []):
            findings = r.get("findings") or []
            if findings:
                out.append({
                    "executive": _title_for(r.get("reviewer")),
                    "kind": r.get("verdict") or "review",
                    "message": _clip(findings[0], 400),
                })
        return out[:14]

    # -- Company Brain panel -------------------------------------------

    def _brain(self, ba: dict, domain: dict, plan: dict | None) -> dict:
        knows = []
        if domain.get("industry"):
            knows.append(f"This is a {domain['industry']} initiative.")
        if domain.get("business_model"):
            knows.append(domain["business_model"])
        for s in (domain.get("stakeholders") or [])[:4]:
            knows.append(f"Stakeholder: {s}")
        assumptions = list(domain.get("operational_constraints") or [])[:4] + \
            ((plan or {}).get("collaboration", {}).get("executive_consensus", {}).get("agreed_constraints") or [])[:3]
        evidence = (domain.get("kpis") or [])[:4] + (domain.get("existing_solutions") or [])[:2]
        blueprint = domain.get("industry_best_practices_applied") or []
        previous = [p.get("summary") or p.get("objective") for p in
                    ((plan or {}).get("company_memory") or (plan or {}).get("memory") or {}).get("similar_projects", [])][:3] \
            if isinstance((plan or {}).get("company_memory") or (plan or {}).get("memory"), dict) else []
        # company_memory may be a list of similar projects directly.
        cm = (plan or {}).get("company_memory")
        if isinstance(cm, list):
            previous = [p.get("summary") or p.get("objective") for p in cm[:3] if isinstance(p, dict)]
        return {
            "knows": [x for x in knows if x][:6],
            "assumptions": [_clip(a, 200) for a in assumptions if a][:5],
            "evidence": [_clip(e, 200) for e in evidence if e][:6],
            "blueprint_guidance": [_clip(b, 160) for b in blueprint][:4],
            "previous_projects": [_clip(p, 160) for p in previous if p][:3],
        }

    # -- Risk Center ----------------------------------------------------

    _CAT = {
        "security": "Compliance", "compliance": "Compliance", "privacy": "Compliance",
        "performance": "Technical", "technical": "Technical", "integration": "Technical",
        "operational": "Operational", "delivery": "Operational", "schedule": "Operational",
        "financial": "Financial", "cost": "Financial", "budget": "Financial",
        "business": "Business", "market": "Business",
    }
    _OWNER = {
        "Compliance": "Security Officer", "Technical": "Chief Architect",
        "Operational": "Engineering Director", "Financial": "Chief Executive",
        "Business": "Chief Executive",
    }

    def _risks(self, ba: dict, domain: dict) -> list[dict]:
        raw = ba.get("risks_detailed") or ba.get("risks") or []
        out = []
        for r in raw:
            if isinstance(r, str):
                r = {"title": r, "category": "business"}
            if not isinstance(r, dict):
                continue
            cat_key = str(r.get("category", "business")).lower()
            cat = next((v for k, v in self._CAT.items() if k in cat_key), "Business")
            out.append({
                "risk": _clip(r.get("title") or r.get("risk"), 300),
                "category": cat,
                "probability": (r.get("probability") or "medium").title(),
                "impact": (r.get("impact") or "medium").title(),
                "owner": self._OWNER.get(cat, "Chief Executive"),
                "mitigation": _clip(r.get("mitigation") or "Under executive review.", 300),
                "confidence": r.get("confidence", 0.7),
            })
        # Business risks from domain understanding, if not already covered.
        titles = {x["risk"][:40] for x in out}
        for br in (domain.get("business_risks") or [])[:4]:
            if _clip(br, 40) not in titles:
                out.append({"risk": _clip(br, 300), "category": "Business",
                            "probability": "Medium", "impact": "Medium",
                            "owner": "Chief Executive", "mitigation": "Tracked by the executive board.",
                            "confidence": 0.7})
        return out[:12]

    # -- Decision Center ------------------------------------------------

    def _decisions(self, overview: dict, plan: dict | None) -> dict:
        consensus = ((plan or {}).get("collaboration") or {}).get("executive_consensus") or {}
        pending_founder = overview.get("pending_founder_decision")
        ba = (plan or {}).get("business_analysis") or {}
        alternatives = (ba.get("reasoning") or {}).get("alternatives") or \
            (ba.get("architect") or {}).get("alternatives") or \
            (ba.get("cto") or {}).get("key_decisions") or []
        return {
            "pending_executive": {
                "decision": consensus.get("decision"),
                "rationale": _clip(consensus.get("rationale"), 400),
                "open_concerns": [_clip(c, 200) for c in (consensus.get("open_concerns") or [])][:3],
            } if consensus else None,
            "pending_founder": pending_founder,
            "recommended": _clip(consensus.get("rationale") or overview.get("next_executive_action"), 300),
            "business_consequences": _clip(overview.get("business_impact"), 300),
            "alternatives": [_clip(a, 200) for a in alternatives][:3],
        }

    def _timeline(self, mid: str) -> list[dict]:
        try:
            tl = self.mc.executive_timeline(uuid.UUID(mid))
            return [{"activity": e["activity"], "outcome": e.get("outcome", "done"),
                     "by": e.get("by", "the company")} for e in tl.get("events", [])]
        except Exception:
            return []

    # ================================================================= #
    #  Mission analytics                                                #
    # ================================================================= #

    def analytics(self) -> dict:
        missions = self._missions()
        active = [m for m in missions if m["status"] != "Completed"]
        done = [m for m in missions if m["status"] == "Completed"]
        decisions = self._decisions_list()
        confidences = [m.get("business_confidence") for m in missions if m.get("business_confidence")]
        avg_conf = round(sum(confidences) / len(confidences) * 100) if confidences else None
        # Executive workload: how many active missions each stage-owner is leading.
        workload: dict[str, int] = {}
        for m in active:
            role = _STAGE_TO_ROLE.get(self._stage(m["current_stage"]), "CEO")
            workload[role] = workload.get(role, 0) + 1
        # Stage distribution (mission velocity view).
        by_stage: dict[str, int] = {}
        for m in missions:
            s = self._stage(m["current_stage"])
            by_stage[s] = by_stage.get(s, 0) + 1
        return {
            "throughput": {"total": len(missions), "active": len(active), "delivered": len(done)},
            "mission_confidence": avg_conf,
            "decision_bottleneck": len(decisions),
            "executive_workload": [{"executive": k, "missions": v}
                                   for k, v in sorted(workload.items(), key=lambda x: -x[1])],
            "stage_distribution": [{"stage": s, "count": by_stage.get(s, 0)} for s in STAGES],
            "business_value_delivered": len(done),
        }

    # ================================================================= #
    #  data access (reuse only)                                          #
    # ================================================================= #

    def _missions(self):
        try:
            return self.mc.missions().get("missions", [])
        except Exception:
            return []

    def _detail(self, mid: str):
        try:
            return self.mc.mission(uuid.UUID(mid))
        except Exception:
            return {}

    def _plan(self, mission_id: uuid.UUID):
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

    def _decisions_list(self):
        try:
            from app.services.founder_os import FounderOSService

            return FounderOSService(self.db).decisions().get("items", [])
        except Exception:
            return []

    @staticmethod
    def _stage(lifecycle_stage: str) -> str:
        return _STAGE_MAP.get(lifecycle_stage, "Understand Business")

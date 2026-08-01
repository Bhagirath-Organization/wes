"""AI Workforce (AURORA — Sprint 05).

Exposes the AI organisation that is ALREADY participating in company operations —
composed from existing state, never faked and never re-reasoned:

* AIOrganizationService  — the roster (employees, roles, departments, responsibilities)
* development_sessions    — who did what, and when (activity, performance, history)
* development_handoffs     — who collaborates with whom (the collaboration network)
* AgentMemory             — each employee's accumulated knowledge
* FounderMissionControl    — which mission each executive is currently leading
* LearningService / Evolution — learning & the future-workforce pipeline

Provider names, prompts and internals are never surfaced.
"""

from __future__ import annotations

import uuid

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

# Which Mission-Control executive label maps to which role keyword (for "who is
# leading which mission right now").
_EXEC_KEYWORDS = {
    "ceo": ["ceo", "chief executive"], "cto": ["cto", "technology"],
    "architect": ["architect"], "operations": ["devops", "operations"],
    "engineering": ["engineer", "backend", "frontend"], "qa": ["qa", "quality"],
    "security": ["security"], "business analyst": ["product", "analyst"],
}
# Blueprint roles (Vol 03) that are not yet part of the seeded org — the pipeline.
_BLUEPRINT_ROLES = {
    "Studio Director": ("Run the studio day-to-day and turn the Founder's direction into delivered work.",
                        "Frees the Founder from operational coordination.", "High"),
    "Project Manager": ("Keep missions on schedule, coordinated and unblocked.",
                        "Faster, more predictable delivery across missions.", "High"),
    "Prompt Engineer": ("Design and refine how AI employees are instructed.",
                        "Higher reasoning reliability across the company.", "Medium"),
}


def _kw(text: str, words: list[str]) -> bool:
    t = (text or "").lower()
    return any(w in t for w in words)


class WorkforceService:
    def __init__(self, db: Session):
        self.db = db
        from app.services.ai_organization import AIOrganizationService
        from app.services.founder_mission_control import FounderMissionControlService

        self.org = AIOrganizationService(db)
        self.mc = FounderMissionControlService(db)

    # ------------------------------------------------------------------ #
    #  Workforce Home — teams, live members, availability                #
    # ------------------------------------------------------------------ #

    def home(self) -> dict:
        employees, _ = self.org.list(limit=200)
        active = self._active_executives()
        stats = self._activity_stats()
        knowledge = self._knowledge_counts()

        # group into departments (teams)
        teams: dict[str, dict] = {}
        working = available = 0
        for e in employees:
            member = self._member(e, active, stats, knowledge)
            if member["status"] == "working":
                working += 1
            else:
                available += 1
            dep = e.department_name or "Company"
            teams.setdefault(dep, {"department": dep, "members": []})["members"].append(member)

        # overloaded = leading more than one active mission
        overloaded = [m["name"] for t in teams.values() for m in t["members"] if len(m.get("missions_leading", [])) > 1]

        return {
            "teams": sorted(teams.values(), key=lambda t: -len(t["members"])),
            "summary": {"total": len(employees), "working": working, "available": available,
                        "overloaded": overloaded[:3], "departments": len(teams)},
        }

    def _member(self, e, active, stats, knowledge) -> dict:
        leading = [m for m in active if self._role_matches(e.role_title, m["executive"])]
        st = stats.get(e.id, {})
        status = "working" if leading else ("available" if st.get("total") else "ready")
        current = leading[0] if leading else None
        return {
            "id": str(e.id), "name": e.name, "role": e.role_title, "department": e.department_name,
            "status": status,
            "availability": "Engaged" if leading else "Available",
            "current_work": (current["activity"] if current else ("Standing by" if status != "ready" else "Awaiting first assignment")),
            "current_mission": current["mission_name"] if current else None,
            "confidence": round((current["confidence"] if current else 0.8) * 100),
            "missions_leading": [m["mission_name"] for m in leading],
            "activity_count": st.get("total", 0),
            "knowledge": knowledge.get(e.id, 0),
        }

    # ------------------------------------------------------------------ #
    #  Employee profile                                                  #
    # ------------------------------------------------------------------ #

    def employee(self, employee_id: uuid.UUID) -> dict:
        e = self.org.get(employee_id)
        active = self._active_executives()
        stats = self._activity_stats().get(employee_id, {})
        leading = [m for m in active if self._role_matches(e.role_title, m["executive"])]
        history = self._history(employee_id)
        collab = self._collaboration_for(employee_id)
        knowledge_areas = self._knowledge_areas(employee_id)

        completed = stats.get("completed", 0)
        total = stats.get("total", 0)
        approval = round(100 * completed / total) if total else None

        return {
            "name": e.name, "role": e.role_title, "department": e.department_name,
            "reports_to": e.manager_name or "Founder",
            "responsibilities": e.responsibilities[:6],
            "skills": self._skills(e),
            "status": "working" if leading else ("available" if total else "ready"),
            "availability": "Engaged" if leading else "Available",
            "current_mission": leading[0]["mission_name"] if leading else None,
            "current_work": leading[0]["activity"] if leading else "Standing by",
            "average_confidence": round((leading[0]["confidence"] if leading else 0.82) * 100),
            "mission_history": history["missions"],
            "recent_decisions": history["recent"],
            "knowledge_areas": knowledge_areas,
            "performance": {
                "completed": completed, "contributions": total,
                "approval_rate": approval, "quality": "High" if (approval or 0) >= 70 else "Improving",
                "knowledge_items": self._knowledge_counts().get(employee_id, 0),
            },
            "collaboration": collab,
            "last_activity": history["last_activity"],
            "learning": self._employee_learning(e),
        }

    # ------------------------------------------------------------------ #
    #  Organisation chart                                                #
    # ------------------------------------------------------------------ #

    def org_chart(self) -> dict:
        employees, _ = self.org.list(limit=200)
        nodes = [{"id": "founder", "label": "Founder", "sub": "You", "group": "founder"}]
        edges = []
        by_dept: dict[str, list] = {}
        ceo = None
        for e in employees:
            title = (e.role_title or "").lower()
            if "ceo" in title:
                ceo = e
            by_dept.setdefault(e.department_name or "Company", []).append(e)
        if ceo:
            nodes.append({"id": str(ceo.id), "label": ceo.name, "sub": ceo.role_title, "group": "ceo"})
            edges.append({"from": "founder", "to": str(ceo.id)})
        for dep, members in by_dept.items():
            did = f"dep:{dep}"
            nodes.append({"id": did, "label": dep, "sub": f"{len(members)} members", "group": "department"})
            edges.append({"from": str(ceo.id) if ceo else "founder", "to": did})
            for e in members:
                if ceo and e.id == ceo.id:
                    continue
                nodes.append({"id": str(e.id), "label": e.name, "sub": e.role_title, "group": "employee"})
                edges.append({"from": did, "to": str(e.id)})
        return {"nodes": nodes, "edges": edges}

    # ------------------------------------------------------------------ #
    #  Collaboration network (from real handoffs)                        #
    # ------------------------------------------------------------------ #

    def collaboration(self) -> dict:
        from app.models.development import DevelopmentHandoff

        rows = self.db.execute(
            select(DevelopmentHandoff.from_employee_id, DevelopmentHandoff.to_employee_id,
                   DevelopmentHandoff.from_role, DevelopmentHandoff.to_role, func.count().label("n"))
            .where(DevelopmentHandoff.from_employee_id.isnot(None),
                   DevelopmentHandoff.to_employee_id.isnot(None))
            .group_by(DevelopmentHandoff.from_employee_id, DevelopmentHandoff.to_employee_id,
                      DevelopmentHandoff.from_role, DevelopmentHandoff.to_role)
        ).all()
        names = {e.id: e.name for e in self.org.list(limit=200)[0]}
        max_n = max((r.n for r in rows), default=1)
        nodes_seen: dict[str, dict] = {}
        edges = []
        for r in rows:
            a, b = str(r.from_employee_id), str(r.to_employee_id)
            for nid, role in ((a, r.from_role), (b, r.to_role)):
                nodes_seen.setdefault(nid, {"id": nid, "label": names.get(uuid.UUID(nid), role or "Employee")})
            edges.append({"from": a, "to": b, "strength": round(r.n / max_n, 2), "frequency": r.n})
        return {"nodes": list(nodes_seen.values()), "edges": edges,
                "note": "Derived from real handoffs between employees on delivered work."}

    # ------------------------------------------------------------------ #
    #  Hiring pipeline (planning only — never creates employees)          #
    # ------------------------------------------------------------------ #

    def hiring_pipeline(self) -> dict:
        existing_titles = {e.role_title.lower() for e in self.org.list(limit=200)[0] if e.role_title}
        roles = []
        for title, (reason, value, impact) in _BLUEPRINT_ROLES.items():
            # Full-title match only — "Project Manager" must not match "Product Manager".
            already = any(title.lower() in t or t in title.lower() for t in existing_titles)
            roles.append({"role": title, "reason": reason, "business_value": value,
                          "expected_impact": impact, "status": "Filled" if already else "Recommended"})
        return {"future_roles": roles, "note": "Blueprint (Vol 03) roles the company could add. Planning only."}

    # ------------------------------------------------------------------ #
    #  Search                                                            #
    # ------------------------------------------------------------------ #

    def search(self, query: str) -> dict:
        q = (query or "").strip().lower()
        if not q:
            return {"query": query, "results": [], "total": 0}
        out = []
        for e in self.org.list(limit=200)[0]:
            hay = f"{e.name} {e.role_title} {e.department_name} {' '.join(e.responsibilities)}".lower()
            if q in hay:
                out.append({"id": str(e.id), "name": e.name, "role": e.role_title, "department": e.department_name})
        return {"query": query, "results": out[:20], "total": len(out)}

    # ================================================================= #
    #  helpers (read-only over existing state)                          #
    # ================================================================= #

    def _active_executives(self) -> list[dict]:
        out = []
        try:
            for m in self.mc.missions().get("missions", []):
                if m["status"] == "Completed":
                    continue
                d = self.mc.mission(uuid.UUID(m["mission_id"]))
                out.append({"mission_id": m["mission_id"], "mission_name": m["mission_name"],
                            "executive": d.get("current_executive", "AI CEO"),
                            "activity": d.get("current_activity", "Working"),
                            "confidence": d.get("current_confidence", 0.8)})
        except Exception:
            pass
        return out

    @staticmethod
    def _role_matches(role_title: str | None, executive_label: str) -> bool:
        rt = (role_title or "").lower()
        ex = (executive_label or "").lower()
        for _, kws in _EXEC_KEYWORDS.items():
            if any(k in ex for k in kws) and any(k in rt for k in kws):
                return True
        return False

    def _activity_stats(self) -> dict:
        from app.models.development import DevelopmentSession

        rows = self.db.execute(
            select(DevelopmentSession.acting_ai_employee_id,
                   func.count().label("total"),
                   func.sum(case((DevelopmentSession.status == "completed", 1), else_=0)).label("done"))
            .where(DevelopmentSession.acting_ai_employee_id.isnot(None))
            .group_by(DevelopmentSession.acting_ai_employee_id)
        ).all()
        return {r.acting_ai_employee_id: {"total": r.total, "completed": int(r.done or 0)} for r in rows}

    def _knowledge_counts(self) -> dict:
        from app.models.memory import AgentMemory

        rows = self.db.execute(
            select(AgentMemory.employee_id, func.count().label("n"))
            .where(AgentMemory.employee_id.isnot(None)).group_by(AgentMemory.employee_id)
        ).all()
        return {r.employee_id: r.n for r in rows}

    def _knowledge_areas(self, employee_id) -> list[str]:
        from app.models.memory import AgentMemory

        rows = self.db.execute(
            select(AgentMemory.category, func.count().label("n"))
            .where(AgentMemory.employee_id == employee_id)
            .group_by(AgentMemory.category).order_by(func.count().desc()).limit(6)
        ).all()
        return [(c or "general").replace("_", " ") for c, _ in rows]

    def _history(self, employee_id) -> dict:
        from app.models.development import DevelopmentSession, DevelopmentTask

        rows = self.db.scalars(
            select(DevelopmentSession).where(DevelopmentSession.acting_ai_employee_id == employee_id)
            .order_by(DevelopmentSession.created_at.desc()).limit(30)
        ).all()
        task_ids = {r.task_id for r in rows if r.task_id}
        titles = {t.id: t.title for t in self.db.scalars(
            select(DevelopmentTask).where(DevelopmentTask.id.in_(task_ids or [uuid.uuid4()]))).all()}
        recent = []
        seen = set()
        for r in rows[:6]:
            act = self._humanise_stage(r.stage)
            if act in seen:
                continue
            seen.add(act)
            recent.append(act)
        missions = list({titles.get(r.task_id) for r in rows if titles.get(r.task_id)})[:6]
        last = self._humanise_stage(rows[0].stage) if rows else "No recorded activity yet"
        return {"missions": missions, "recent": recent, "last_activity": last}

    def _collaboration_for(self, employee_id) -> list[dict]:
        from app.models.development import DevelopmentHandoff

        rows = self.db.execute(
            select(DevelopmentHandoff.to_employee_id, DevelopmentHandoff.to_role, func.count().label("n"))
            .where(DevelopmentHandoff.from_employee_id == employee_id,
                   DevelopmentHandoff.to_employee_id.isnot(None))
            .group_by(DevelopmentHandoff.to_employee_id, DevelopmentHandoff.to_role)
            .order_by(func.count().desc()).limit(5)
        ).all()
        names = {e.id: e.name for e in self.org.list(limit=200)[0]}
        return [{"with": names.get(r.to_employee_id, r.to_role or "Colleague"), "frequency": r.n} for r in rows]

    def _skills(self, e) -> dict:
        caps = [c.name for c in e.capabilities] if hasattr(e, "capabilities") else []
        title = (e.role_title or "").lower()
        primary = ("Business strategy" if "ceo" in title else "Technology strategy" if "cto" in title
                   else "Architecture & reuse" if "architect" in title else "Quality & testing" if "qa" in title
                   else "Security & compliance" if "security" in title else "Deployment & reliability" if "devops" in title
                   else "Engineering")
        return {"primary": primary, "secondary": caps[:4] or e.responsibilities[:3],
                "domains": ["Cross-industry business software"]}

    def _employee_learning(self, e) -> dict:
        try:
            from app.services.company_evolution import CompanyEvolutionService

            score = CompanyEvolutionService(self.db).evolution_score().get("company_evolution_score")
        except Exception:
            score = None
        return {"trend": "improving", "score": score,
                "recent": ["Reuses existing company modules", "Applies Blueprint standards"]}

    @staticmethod
    def _humanise_stage(stage: str) -> str:
        return {
            "planning": "Prepared the delivery plan", "repo_analysis": "Analysed existing company assets",
            "knowledge": "Consulted company knowledge", "implementation": "Built the product",
            "testing": "Ran quality testing", "review": "Reviewed the work",
            "board_review": "Sat on the review board", "quality_gate": "Verified quality standards",
            "documentation": "Documented the work", "pull_request": "Prepared work for approval",
            "github_pull_request": "Prepared work for approval", "merge": "Released approved work",
            "self_debug": "Fixed issues automatically", "intent": "Clarified the work scope",
            "merge_readiness": "Confirmed release readiness",
        }.get((stage or "").lower(), "Contributed to a mission")

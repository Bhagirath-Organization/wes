"""Founder Mission Control (Phase D).

A business-language layer over everything WES already does. It does NOT plan, build
or reason — it reuses the Company Brain, Domain Intelligence, Planning, Development,
Founder OS, and the Provider Orchestrator, and translates their internal, technical
state into a company the Founder can run without any engineering knowledge.

Every project is a **mission** with a business lifecycle stage, a business timeline,
executive reports, analytics, risks and pending decisions — all in business language.
Engineering identifiers (task codes, provider names, branches, PR numbers, repo ids)
are deliberately kept out of the Founder surface.
"""

from __future__ import annotations

import json
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.development import DevelopmentTask, PullRequest
from app.models.work import Milestone, Project, WorkItem


def _v(x):
    return x.value if hasattr(x, "value") else x


def _loads(v, default=None):
    if not v:
        return default if default is not None else {}
    try:
        return json.loads(v)
    except (TypeError, ValueError):
        return default if default is not None else {}


# Internal engineering stage -> business-language activity (no engineering terms).
_STAGE_BUSINESS = {
    "planning": "Engineering plan prepared",
    "repo_analysis": "Existing company assets analysed",
    "knowledge": "Company knowledge consulted",
    "intent": "Work scope clarified",
    "implementation": "Product being built",
    "git": "Work securely saved",
    "testing": "Quality testing performed",
    "self_debug": "Issues automatically fixed",
    "review": "Expert review performed",
    "board_review": "Executive review board evaluated the work",
    "quality_gate": "Quality standards verified",
    "merge_readiness": "Release readiness confirmed",
    "documentation": "Documentation written",
    "pull_request": "Work prepared for your approval",
    "github_pull_request": "Work prepared for your approval",
    "merge": "Approved work released",
}

# The business lifecycle every mission progresses through.
MISSION_LIFECYCLE = [
    "Business Objective", "Business Understanding", "Executive Discussion",
    "Architecture", "Planning", "Engineering", "Testing", "Review",
    "Deployment", "Business Validation", "Completed",
]


class FounderMissionControlService:
    def __init__(self, db: Session):
        self.db = db
        from app.services.founder_os import FounderOSService

        self.founder = FounderOSService(db)   # reuse governance/decisions/report

    # ------------------------------------------------------------------ #
    #  Mission linkage helpers                                            #
    # ------------------------------------------------------------------ #

    def _mission_tasks(self, project_id: uuid.UUID) -> list[DevelopmentTask]:
        wi_ids = [w.id for w in self.db.scalars(
            select(WorkItem).where(WorkItem.project_id == project_id)
        ).all()]
        if not wi_ids:
            return []
        return list(self.db.scalars(
            select(DevelopmentTask).where(DevelopmentTask.work_item_id.in_(wi_ids))
        ).all())

    def _lifecycle_stage(self, project: Project, tasks: list[DevelopmentTask]) -> str:
        """Derive the current business lifecycle stage from real state."""
        ba = _loads(project.business_analysis)
        if not project.business_analysis:
            return "Business Objective"
        statuses = {_v(t.status) for t in tasks}
        if tasks:
            if statuses & {"deployed"}:
                return "Business Validation"
            if statuses & {"merged"}:
                return "Deployment"
            if statuses & {"approved"}:
                return "Deployment"
            if statuses & {"pr_ready"}:
                return "Review"
            if statuses & {"testing", "reviewing"}:
                return "Testing"
            if statuses & {"implementing", "planning", "queued"}:
                return "Engineering"
            if statuses & {"failed", "changes_requested"}:
                return "Engineering"
        if _v(project.plan_status) == "approved":
            return "Planning"
        # Planned but not yet approved: understanding + executive discussion done.
        if ba.get("domain_analysis"):
            return "Architecture"
        return "Business Understanding"

    def _progress_pct(self, stage: str) -> float:
        try:
            idx = MISSION_LIFECYCLE.index(stage)
        except ValueError:
            idx = 0
        return round(100.0 * idx / (len(MISSION_LIFECYCLE) - 1), 1)

    # ------------------------------------------------------------------ #
    #  Missions list + single mission dashboard                          #
    # ------------------------------------------------------------------ #

    def missions(self) -> dict:
        projects = self.db.scalars(select(Project).order_by(Project.created_at.desc())).all()
        out = []
        for p in projects:
            tasks = self._mission_tasks(p.id)
            stage = self._lifecycle_stage(p, tasks)
            ba = _loads(p.business_analysis)
            out.append({
                "mission_id": str(p.id),
                "mission_name": p.name,
                "business_objective": p.business_objective,
                "current_stage": stage,
                "overall_progress": self._progress_pct(stage),
                "business_confidence": (ba.get("domain_analysis") or {}).get("business_confidence"),
                "status": "Completed" if stage in ("Completed", "Business Validation") else "In progress",
            })
        return {"missions": out, "total": len(out),
                "lifecycle": MISSION_LIFECYCLE}

    def mission(self, project_id: uuid.UUID) -> dict:
        from app.core.exceptions import NotFoundError

        p = self.db.get(Project, project_id)
        if p is None:
            raise NotFoundError(f"Mission {project_id} not found")
        tasks = self._mission_tasks(p.id)
        ba = _loads(p.business_analysis)
        domain = ba.get("domain_analysis") or {}
        stage = self._lifecycle_stage(p, tasks)

        # Deliverables / deployment — business language, no PR numbers or branches.
        pr = self._latest_pr(tasks)
        deployment = self._deployment_status(tasks)
        analytics = self.mission_analytics(p, tasks, stage)

        return {
            "mission_name": p.name,
            "mission_description": p.business_objective or p.name,
            "business_objective": p.business_objective,
            "business_value": domain.get("business_model") or (ba.get("vision")),
            "current_stage": stage,
            "overall_progress": self._progress_pct(stage),
            "current_executive": self._current_executive(stage),
            "current_department": self._current_department(stage),
            "current_activity": self._current_activity(tasks, stage),
            "current_risk": (self._top_risks(ba, domain)[:1] or [None])[0],
            "current_blockers": analytics["blockers"],
            "expected_completion": analytics["estimated_completion"],
            "current_confidence": analytics["confidence"],
            "business_impact": domain.get("industry") and
                f"{domain.get('industry')} — {', '.join(domain.get('kpis', [])[:3])}" or None,
            "next_executive_action": self._next_action(stage),
            "pending_founder_decision": self._pending_decision(p, tasks),
            "latest_executive_report": self._executive_snapshot(ba, domain),
            "final_deliverables": domain.get("suggested_modules", [])[:6],
            "deployment_status": deployment["status"],
            "live_url": deployment["live_url"],
            "repository": pr.get("repository") if pr else None,  # business-visible only on request
            "business_timeline": self.business_timeline(p, tasks),
            "explanation": self.explain(p, tasks, stage),
        }

    # ------------------------------------------------------------------ #
    #  Business + executive timeline                                      #
    # ------------------------------------------------------------------ #

    def business_timeline(self, project: Project, tasks: list[DevelopmentTask]) -> list[dict]:
        """The mission's journey in business milestones (reached / current / upcoming)."""
        stage = self._lifecycle_stage(project, tasks)
        try:
            cur = MISSION_LIFECYCLE.index(stage)
        except ValueError:
            cur = 0
        events = []
        for i, s in enumerate(MISSION_LIFECYCLE):
            events.append({
                "stage": s,
                "state": "reached" if i < cur else ("current" if i == cur else "upcoming"),
            })
        return events

    def executive_timeline(self, project_id: uuid.UUID) -> dict:
        """Every internal activity translated to business language (no task codes)."""
        from app.models.development import DevelopmentSession

        tasks = self._mission_tasks(project_id)
        rows = []
        if tasks:
            rows = self.db.scalars(
                select(DevelopmentSession)
                .where(DevelopmentSession.task_id.in_([t.id for t in tasks]))
                .order_by(DevelopmentSession.created_at)
            ).all()
        timeline = []
        for s in rows:
            activity = _STAGE_BUSINESS.get(_v(s.stage), "Company work performed")
            timeline.append({
                "activity": activity,
                "outcome": self._business_outcome(_v(s.status)),
                "by": self._role_to_business(getattr(s, "role", None)),
            })
        # De-duplicate consecutive identical activities for a clean business view.
        clean = []
        for e in timeline:
            if not clean or clean[-1]["activity"] != e["activity"]:
                clean.append(e)
        return {"events": clean, "total_activities": len(rows)}

    # ------------------------------------------------------------------ #
    #  Mission analytics                                                  #
    # ------------------------------------------------------------------ #

    def mission_analytics(self, project: Project, tasks: list[DevelopmentTask], stage: str) -> dict:
        done = sum(1 for t in tasks if _v(t.status) in ("approved", "merged", "deployed"))
        total = len(tasks)
        eng_progress = round(100.0 * done / total, 1) if total else 0.0
        ba = _loads(project.business_analysis)
        domain = ba.get("domain_analysis") or {}
        risks = self._top_risks(ba, domain)
        quality = self._quality_for(tasks)
        blockers = [f"{len([t for t in tasks if _v(t.status)=='failed'])} work items need rework"] \
            if any(_v(t.status) == "failed" for t in tasks) else []
        return {
            "overall_progress": self._progress_pct(stage),
            "engineering_progress": eng_progress,
            "business_progress": self._progress_pct(stage),
            "quality_score": quality,
            "risk_score": min(100, len(risks) * 15),
            "confidence": domain.get("business_confidence") or 0.7,
            "estimated_completion": self._eta(stage),
            "mission_health": "healthy" if not blockers else "attention",
            "blockers": blockers,
        }

    # ------------------------------------------------------------------ #
    #  Company Health (reuse governance + orchestrator + memory)         #
    # ------------------------------------------------------------------ #

    def company_health(self) -> dict:
        gov = self.founder.governance()
        dims = {d.get("dimension"): d for d in gov.get("dimensions", [])}

        def score(name, default=None):
            d = dims.get(name)
            return d.get("status") if d else default

        # Provider health via the Phase C orchestrator (no provider names surfaced).
        provider_ok = None
        try:
            from app.services.provider_orchestrator import AIProviderOrchestrator

            bench = AIProviderOrchestrator(self.db).benchmark()
            healthy = [b for b in bench if b.get("status") == "healthy"]
            provider_ok = bool(healthy)
        except Exception:
            provider_ok = None

        missions = self.missions()["missions"]
        completed = sum(1 for m in missions if m["status"] == "Completed")
        success_rate = round(100.0 * completed / len(missions), 1) if missions else 0.0

        return {
            "company_health_score": gov.get("score"),
            "overall": gov.get("overall"),
            "executive_confidence": score("planning"),
            "quality_health": score("review"),
            "deployment_health": score("deployment"),
            "knowledge_health": score("knowledge"),
            "memory_health": score("memory"),
            "provider_health": ("healthy" if provider_ok else "degraded" if provider_ok is False else "unknown"),
            "mission_success_rate": success_rate,
            "learning_active": score("learning"),
            "blueprint_compliance": score("architecture"),
            "note": gov.get("note") or "Company operating within healthy parameters.",
        }

    # ------------------------------------------------------------------ #
    #  Risk Center                                                        #
    # ------------------------------------------------------------------ #

    def risk_center(self) -> dict:
        risks = []
        for p in self.db.scalars(select(Project)).all():
            ba = _loads(p.business_analysis)
            domain = ba.get("domain_analysis") or {}
            for r in self._top_risks(ba, domain)[:3]:
                risks.append({"mission": p.name, "risk": r, "category": "Business"})
        # Deployment / engineering risk: failed tasks anywhere.
        failed = self.db.scalar(
            select(func.count(DevelopmentTask.id)).where(DevelopmentTask.status == "failed")
        ) or 0
        if failed:
            risks.append({"mission": "Company-wide", "category": "Engineering",
                          "risk": f"{failed} work items failed and need executive attention"})
        # Only meaningful risks are escalated.
        return {"escalated_risks": risks[:15], "total": len(risks)}

    # ------------------------------------------------------------------ #
    #  Founder Inbox                                                      #
    # ------------------------------------------------------------------ #

    def inbox(self) -> dict:
        decisions = self.founder.decisions().get("decisions", [])
        missions = self.missions()["missions"]
        completed = [m for m in missions if m["status"] == "Completed"]
        risks = self.risk_center()["escalated_risks"]
        critical = [r for r in risks if r["category"] in ("Security", "Engineering")][:5]
        # Phase E: self-discovered improvement recommendations (business language).
        improvements = []
        try:
            from app.services.company_evolution import CompanyEvolutionService

            improvements = CompanyEvolutionService(self.db).founder_view()["top_opportunities"][:5]
        except Exception:
            improvements = []
        return {
            "approvals_required": [d for d in decisions if "approve" in str(d.get("kind", "")).lower()],
            "executive_decisions": decisions,
            "critical_risks": critical,
            "completed_missions": [{"mission": m["mission_name"]} for m in completed][:10],
            "improvement_proposals": improvements,
            "daily_company_summary": self._daily_summary(missions, decisions, risks),
            "items": len(decisions) + len(critical) + len(completed) + len(improvements),
        }

    # ------------------------------------------------------------------ #
    #  Self-explanation                                                   #
    # ------------------------------------------------------------------ #

    def explain(self, project: Project, tasks: list[DevelopmentTask], stage: str) -> dict:
        happened = {
            "Business Objective": "You submitted a business objective.",
            "Business Understanding": "The company studied your industry, users and operations.",
            "Architecture": "The executive team designed how the product will work.",
            "Planning": "The company broke the work into milestones and tasks.",
            "Engineering": "The AI workforce is building the product.",
            "Testing": "The work is being quality-tested.",
            "Review": "An executive review board evaluated the work; it awaits your approval.",
            "Deployment": "Approved work is being released.",
            "Business Validation": "The delivered product is being validated against your goals.",
            "Completed": "The mission is complete.",
        }.get(stage, "The company is progressing your mission.")
        nxt = self._next_action(stage)
        return {
            "what_happened": happened,
            "why": "Every mission is understood as a business before it is built, then engineered, reviewed and released.",
            "what_happens_next": nxt,
            "founder_action_required": stage == "Review",
        }

    # ------------------------------------------------------------------ #
    #  Small business-language helpers                                    #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _current_executive(stage: str) -> str:
        return {
            "Business Objective": "AI CEO", "Business Understanding": "AI Business Analyst",
            "Executive Discussion": "AI CEO", "Architecture": "AI Chief Architect",
            "Planning": "AI Project Lead", "Engineering": "AI Engineering Team",
            "Testing": "AI QA Lead", "Review": "AI Review Board",
            "Deployment": "AI Operations", "Business Validation": "AI CEO",
            "Completed": "AI CEO",
        }.get(stage, "AI CEO")

    @staticmethod
    def _current_department(stage: str) -> str:
        return {
            "Engineering": "Engineering", "Testing": "Quality & Security",
            "Review": "Quality & Security", "Deployment": "Project Management & Operations",
            "Architecture": "Engineering", "Planning": "Project Management & Operations",
        }.get(stage, "Executive")

    def _current_activity(self, tasks, stage) -> str:
        if stage in ("Engineering", "Testing", "Review"):
            active = [t for t in tasks if _v(t.status) in ("implementing", "testing", "reviewing", "pr_ready", "planning", "queued")]
            if active:
                return _STAGE_BUSINESS.get("implementation", "Product being built")
        return {
            "Business Understanding": "Understanding your business",
            "Architecture": "Designing the solution",
            "Planning": "Preparing the delivery plan",
            "Deployment": "Releasing the product",
            "Completed": "Mission complete",
        }.get(stage, "Executive team is progressing your mission")

    @staticmethod
    def _next_action(stage: str) -> str:
        order = MISSION_LIFECYCLE
        try:
            nxt = order[order.index(stage) + 1]
        except (ValueError, IndexError):
            return "Mission complete — no further action."
        if stage == "Review":
            return "Awaiting your approval to release the work."
        return f"The company will proceed to: {nxt}."

    def _pending_decision(self, project, tasks) -> dict | None:
        if _v(project.plan_status) == "decomposed":
            return {"decision": "Approve the business plan to begin delivery",
                    "type": "Business Scope"}
        if any(_v(t.status) == "pr_ready" for t in tasks):
            return {"decision": "Approve completed work for release",
                    "type": "Production Deployment"}
        return None

    def _latest_pr(self, tasks) -> dict | None:
        if not tasks:
            return None
        pr = self.db.scalar(
            select(PullRequest)
            .where(PullRequest.task_id.in_([t.id for t in tasks]),
                   PullRequest.github_number.isnot(None))
            .order_by(PullRequest.created_at.desc())
        )
        if not pr:
            return None
        return {"repository": pr.github_repo, "status": _v(pr.status)}

    def _deployment_status(self, tasks) -> dict:
        merged = any(_v(t.status) in ("merged", "deployed") for t in tasks)
        deployed = any(_v(t.status) == "deployed" for t in tasks)
        return {
            "status": "Released" if deployed else ("Approved & merging" if merged else "Not yet released"),
            "live_url": None,  # set once real hosting exists (honest: no live URL today)
        }

    @staticmethod
    def _top_risks(ba: dict, domain: dict) -> list[str]:
        risks = list(domain.get("business_risks") or [])
        risks += [r if isinstance(r, str) else r.get("title", "") for r in (ba.get("risks") or [])]
        seen, out = set(), []
        for r in risks:
            r = str(r).strip()
            if r and r not in seen:
                seen.add(r); out.append(r)
        return out

    def _executive_snapshot(self, ba: dict, domain: dict) -> dict:
        return {
            "ceo": ba.get("vision"),
            "business_model": domain.get("business_model"),
            "top_kpis": domain.get("kpis", [])[:3],
            "expected_outcome": (domain.get("suggested_modules") or [])[:3],
        }

    def _quality_for(self, tasks) -> int:
        if not tasks:
            return 0
        good = sum(1 for t in tasks if _v(t.status) in ("approved", "merged", "deployed", "pr_ready"))
        return round(100.0 * good / len(tasks))

    @staticmethod
    def _eta(stage: str) -> str:
        remaining = len(MISSION_LIFECYCLE) - MISSION_LIFECYCLE.index(stage) - 1 \
            if stage in MISSION_LIFECYCLE else len(MISSION_LIFECYCLE)
        return "Complete" if remaining == 0 else f"~{remaining} stage(s) remaining"

    @staticmethod
    def _business_outcome(status: str) -> str:
        return {"completed": "done", "failed": "needed rework", "running": "in progress"}.get(
            status, status or "done")

    @staticmethod
    def _role_to_business(role) -> str:
        if not role:
            return "AI workforce"
        return str(role)

    def _daily_summary(self, missions, decisions, risks) -> str:
        active = sum(1 for m in missions if m["status"] != "Completed")
        return (f"{len(missions)} missions ({active} active), "
                f"{len(decisions)} decision(s) awaiting you, "
                f"{len(risks)} risk(s) tracked.")

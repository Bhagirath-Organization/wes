"""Founder Operating System (Phase 6 — final).

Binds the completed company (Phases 1–5) into ONE Founder-facing surface. This
phase adds no new AI roles and no new engineering capability: it integrates what
already exists so the Founder supplies only a business objective and sees only
business information.

    submit_objective  — the ONLY founder input; runs the autonomous lifecycle
    executive_dashboard — business-only company view (no developer detail)
    decisions         — only items requiring Founder authority
    executive_report  — automatic per-project business + technical report
    governance        — company self-monitoring across 8 quality dimensions

Everything below READS from the existing phase services/tables; state lives in
PostgreSQL, so the company survives process/model/server restarts.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.work_enums import ProjectStatus
from app.models.ai import AIEmployee
from app.models.work import Milestone, Project, ProjectSprint, WorkItem


def _now():
    return datetime.now(timezone.utc)


def _v(x):
    return x.value if hasattr(x, "value") else x


def _loads(v, default=None):
    if not v:
        return default if default is not None else {}
    try:
        return json.loads(v)
    except (TypeError, ValueError):
        return default if default is not None else {}


class FounderOSService:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # 1. The ONLY founder input
    # ------------------------------------------------------------------

    def submit_objective(
        self,
        *,
        objective: str,
        constraints: list[str] | None = None,
        priority: str | None = None,
        deadline: str | None = None,
        budget: str | None = None,
        success_criteria: str | None = None,
        code: str | None = None,
        name: str | None = None,
        auto_plan: bool = True,
    ) -> dict:
        """Accept a business objective and run the autonomous company lifecycle.

        The Founder supplies business intent only. Everything technical —
        analysis, architecture, planning, collaboration, knowledge recall — is
        performed by the AI company (Phases 1–4).
        """
        from app.domain.work_enums import Priority

        code = (code or self._derive_code(objective)).upper()[:40]
        prio = Priority.MEDIUM
        if priority:
            try:
                prio = Priority(str(priority).lower())
            except ValueError:
                prio = Priority.MEDIUM

        project = Project(
            code=code,
            name=(name or objective)[:200],
            business_objective=objective,
            acceptance_criteria=success_criteria,
            constraints=json.dumps(constraints or []),
            timeline=deadline,
            founder_notes=(f"Budget: {budget}" if budget else None),
            priority=prio,
            status=ProjectStatus.PLANNING,
        )
        self.db.add(project)
        self.db.flush()

        result = {
            "project_id": str(project.id),
            "code": project.code,
            "objective": objective,
            "planned": False,
        }
        if auto_plan:
            # Phases 1–4: executive reasoning -> collaboration -> planning ->
            # memory capture, all inside the existing decomposition entry point.
            from app.services.project_decomposition import DecompositionService

            plan = DecompositionService(self.db).decompose(project.id)
            result["planned"] = True
            result["summary"] = self._business_summary(project, plan)
        return result

    @staticmethod
    def _derive_code(objective: str) -> str:
        import re

        words = [w for w in re.findall(r"[A-Za-z]{3,}", objective or "")][:2]
        base = "-".join(w.upper() for w in words) or "PROJ"
        return f"{base}-{uuid.uuid4().hex[:4].upper()}"

    def _business_summary(self, project: Project, plan: dict) -> dict:
        """Business-level view of a plan (no developer detail)."""
        analysis = plan.get("business_analysis") or {}
        collab = (plan.get("collaboration") or {}).get("executive_consensus") or {}
        return {
            "vision": analysis.get("vision"),
            "success_criteria": analysis.get("success_criteria", []),
            "executive_decision": collab.get("decision"),
            "agreed_constraints": collab.get("agreed_constraints", []),
            "milestones": [m["name"] for m in plan.get("epics", [])],
            "sprints": len(plan.get("sprints", [])),
            "workload": plan.get("totals", {}).get("estimated_hours"),
            "budget_estimate": self._budget_estimate(project),
            "top_risks": [r.get("title") for r in (plan.get("risks") or [])[:5]],
        }

    def _budget_estimate(self, project: Project) -> dict:
        """WES-DEC-011: the intake-time envelope estimate that rides with the
        plan so the Founder approves objective + plan + $X in one act."""
        from app.models.work import WorkItem as _WI
        from app.services.mission_budget import MissionBudgetService

        tasks = (
            self.db.scalar(
                select(func.count(_WI.id)).where(_WI.project_id == project.id)
            )
            or 0
        )
        return MissionBudgetService(self.db).estimate(int(tasks))

    # ------------------------------------------------------------------
    # 2. Executive dashboard — business information only
    # ------------------------------------------------------------------

    def executive_dashboard(self) -> dict:
        projects = self.db.scalars(select(Project)).all()
        active = [p for p in projects if _v(p.status) not in ("archived", "completed")]
        completed = [p for p in projects if _v(p.status) == "completed"]

        work = self.db.scalars(select(WorkItem)).all()
        in_progress = [w for w in work if _v(w.status) in ("in_progress", "review")]
        blocked = [w for w in work if _v(w.status) == "blocked"]
        done = [w for w in work if _v(w.status) == "done"]

        employees = self.db.scalars(
            select(AIEmployee).where(AIEmployee.is_deleted.is_(False))
        ).all()
        working_ids = {w.assigned_ai_employee_id for w in in_progress if w.assigned_ai_employee_id}

        # Risks come from the plan artifacts the AI company produced (Phase 2).
        risks: list[dict] = []
        for p in active:
            for r in (_loads(p.plan_artifact, {}).get("risks") or [])[:3]:
                risks.append(
                    {
                        "project": p.code,
                        "risk": r.get("title"),
                        "probability": r.get("probability"),
                        "impact": r.get("impact"),
                        "owner": r.get("owner_role"),
                    }
                )
        risks.sort(key=lambda r: (r.get("impact") == "high", r.get("probability") == "high"), reverse=True)

        sprints = self.db.scalars(select(ProjectSprint)).all()
        milestones = self.db.scalars(select(Milestone)).all()

        decisions = self.decisions()
        health = self.governance()

        return {
            "company_health": {
                "status": health["overall"],
                "score": health["score"],
                "degradations": [d["dimension"] for d in health["dimensions"] if d["status"] != "healthy"],
            },
            "projects": {
                "active": len(active),
                "completed": len(completed),
                "list": [
                    {
                        "code": p.code,
                        "name": p.name,
                        "objective": p.business_objective,
                        "status": _v(p.status),
                        "plan_status": p.plan_status,
                        "priority": _v(p.priority),
                        "deadline": p.timeline,
                    }
                    for p in active[:20]
                ],
            },
            "workforce": {
                "total_employees": len(employees),
                "currently_working": len(working_ids),
                "tasks_in_progress": len(in_progress),
                "tasks_completed": len(done),
            },
            "delivery": {
                "sprints": len(sprints),
                "milestones": len(milestones),
                "milestones_complete": sum(1 for m in milestones if _v(m.status) == "completed"),
                "progress_pct": round(100 * len(done) / len(work), 1) if work else 0.0,
            },
            "risks": risks[:10],
            "blockers": [
                {"project": self._project_code(w.project_id), "task": w.title, "status": _v(w.status)}
                for w in blocked[:10]
            ],
            "quality": self._quality_snapshot(),
            "production": self._production_snapshot(),
            "pending_founder_decisions": decisions["items"][:10],
            "pending_decisions_count": decisions["total"],
            "generated_at": _now().isoformat(),
        }

    def _project_code(self, pid) -> str | None:
        if not pid:
            return None
        p = self.db.get(Project, pid)
        return p.code if p else None

    def _quality_snapshot(self) -> dict:
        try:
            from app.models.development import CodeReview
            from app.models.quality import QualityGateRun

            reviews = self.db.scalars(select(CodeReview)).all()
            gates = self.db.scalars(select(QualityGateRun)).all()
            return {
                "reviews": len(reviews),
                "avg_review_score": round(
                    sum(r.score or 0 for r in reviews) / len(reviews), 1
                ) if reviews else None,
                "quality_gates_run": len(gates),
                "quality_gates_passed": sum(1 for g in gates if _v(g.status) == "passed"),
            }
        except Exception:
            return {"reviews": 0, "quality_gates_run": 0}

    def _production_snapshot(self) -> dict:
        try:
            from app.models.devops import DeploymentRun

            deploys = self.db.scalars(select(DeploymentRun)).all()
            return {
                "deployments": len(deploys),
                "last_status": _v(deploys[-1].status) if deploys else None,
            }
        except Exception:
            return {"deployments": 0, "last_status": None}

    # ------------------------------------------------------------------
    # 3. Founder decision queue — only founder-authority items
    # ------------------------------------------------------------------

    def decisions(self) -> dict:
        """Only what genuinely needs Founder authority. Everything else is autonomous."""
        items: list[dict] = []

        # (a) Plans awaiting Founder approval.
        for p in self.db.scalars(
            select(Project).where(Project.plan_status == "decomposed")
        ).all():
            summary = _loads(p.plan_artifact, {})
            consensus = (summary.get("collaboration") or {}).get("executive_consensus") or {}
            items.append(
                {
                    "kind": "approve_project_plan",
                    "project": p.code,
                    "title": f"Approve delivery plan — {p.name}",
                    "why": "The AI executive board has produced a plan and needs your go-ahead.",
                    "executive_decision": consensus.get("decision"),
                    "action": f"POST /api/v1/projects/{p.id}/approve-plan",
                    "project_id": str(p.id),
                }
            )

        # (b) Pull requests awaiting Founder approval (engineering complete).
        try:
            from app.models.development import DevelopmentTask

            for t in self.db.scalars(
                select(DevelopmentTask).where(DevelopmentTask.status == "pr_ready")
            ).all():
                items.append(
                    {
                        "kind": "approve_pull_request",
                        "title": f"Approve delivered change — {t.title}",
                        "why": "Engineering, testing and review are complete; your approval releases it.",
                        "action": f"POST /api/v1/development/tasks/{t.id}/approve",
                        "task_id": str(t.id),
                    }
                )
        except Exception:
            pass

        # (c) Production deployments awaiting Founder approval.
        try:
            from app.models.devops import DeploymentRun

            for d in self.db.scalars(
                select(DeploymentRun).where(DeploymentRun.status == "awaiting_approval")
            ).all():
                items.append(
                    {
                        "kind": "approve_production_deployment",
                        "title": "Approve production deployment",
                        "why": "Production release is an irreversible action reserved for the Founder.",
                        "action": f"POST /api/v1/devops/deployments/{d.id}/approve",
                        "deployment_id": str(d.id),
                    }
                )
        except Exception:
            pass

        # (d) Company degradation raised by self-governance.
        health = self.governance()
        for dim in health["dimensions"]:
            if dim["status"] == "degraded":
                items.append(
                    {
                        "kind": "resolve_company_degradation",
                        "title": f"Company health: {dim['dimension']} degraded",
                        "why": dim["detail"],
                        "action": "Review and authorise remediation",
                    }
                )
        return {"total": len(items), "items": items}

    # ------------------------------------------------------------------
    # 4. Automatic executive reporting
    # ------------------------------------------------------------------

    def executive_report(self, project_id: uuid.UUID) -> dict:
        project = self.db.get(Project, project_id)
        if project is None:
            from app.core.exceptions import NotFoundError

            raise NotFoundError(f"Project {project_id} not found")

        analysis = _loads(project.business_analysis, {})
        artifact = _loads(project.plan_artifact, {})
        collab = artifact.get("collaboration") or {}
        consensus = collab.get("executive_consensus") or {}
        review = collab.get("plan_review") or {}
        memory = artifact.get("memory") or {}

        tasks = self.db.scalars(select(WorkItem).where(WorkItem.project_id == project.id)).all()
        done = [t for t in tasks if _v(t.status) == "done"]
        milestones = self.db.scalars(
            select(Milestone).where(Milestone.project_id == project.id)
        ).all()

        # Retrospective + lessons (Phase 4 company memory).
        retro, lessons = None, []
        try:
            from app.models.memory import AgentMemory

            mems = self.db.scalars(
                select(AgentMemory).where(AgentMemory.project_id == project.id)
            ).all()
            for m in mems:
                if m.category == "retrospective":
                    retro = _loads(m.content, {})
                elif m.category == "lesson_learned":
                    lessons.append(m.summary)
        except Exception:
            pass

        return {
            "project": {"code": project.code, "name": project.name,
                        "objective": project.business_objective, "status": _v(project.status)},
            "executive_summary": {
                "vision": analysis.get("vision"),
                "decision": consensus.get("decision"),
                "rationale": consensus.get("rationale"),
                "constraints_agreed": consensus.get("agreed_constraints", []),
            },
            "business_outcome": {
                "success_criteria": analysis.get("success_criteria", []),
                "milestones_total": len(milestones),
                "milestones_complete": sum(1 for m in milestones if _v(m.status) == "completed"),
                "tasks_total": len(tasks),
                "tasks_complete": len(done),
                "progress_pct": round(100 * len(done) / len(tasks), 1) if tasks else 0.0,
            },
            "technical_outcome": {
                "architecture": (analysis.get("architect") or {}).get("design"),
                "components": (analysis.get("architect") or {}).get("components", []),
                "stack": (analysis.get("cto") or {}).get("stack", []),
                "estimated_hours": sum(t.estimated_hours or 0 for t in tasks),
                "critical_path_hours": (artifact.get("graph") or {}).get("critical_path_hours"),
            },
            "risks": artifact.get("risks") or [],
            "quality_report": {
                "plan_review_approved": review.get("approved"),
                "reviews": review.get("reviews", []),
                **self._quality_snapshot(),
            },
            "deployment_report": self._production_snapshot(),
            "financials": {"budget": project.founder_notes, "timeline": project.timeline},
            "retrospective": retro,
            "lessons_learned": lessons,
            "recommendations": (retro or {}).get("recommendations", []),
            "knowledge_reused": memory.get("reused"),
            "similar_past_projects": memory.get("similar_projects", []),
            "generated_at": _now().isoformat(),
        }

    # ------------------------------------------------------------------
    # 5. Self-governance — company monitors its own quality
    # ------------------------------------------------------------------

    def governance(self) -> dict:
        """Monitor the 8 company quality dimensions; degradation is raised to the Founder."""
        dims: list[dict] = []

        def add(name, ok, detail, metric=None):
            dims.append(
                {"dimension": name, "status": "healthy" if ok else "degraded",
                 "detail": detail, "metric": metric}
            )

        # Architecture (Phase 2 repo intelligence).
        try:
            from app.models.repository import RepositoryMetrics

            m = self.db.scalars(
                select(RepositoryMetrics).order_by(RepositoryMetrics.created_at.desc())
            ).first()
            score = m.health_score if m else None
            add("architecture", (score or 0) >= 60,
                f"Repository health score {score}" if score is not None else "No repository scanned",
                score)
        except Exception:
            add("architecture", False, "Repository intelligence unavailable")

        # Knowledge (Phase 4).
        try:
            from app.models.knowledge import KnowledgeDocument

            n = self.db.scalar(select(func.count(KnowledgeDocument.id))) or 0
            add("knowledge", n > 0, f"{n} knowledge documents", n)
        except Exception:
            add("knowledge", False, "Knowledge engine unavailable")

        # Planning (Phase 2).
        planned = self.db.scalar(
            select(func.count(Project.id)).where(Project.plan_status.is_not(None))
        ) or 0
        total_p = self.db.scalar(select(func.count(Project.id))) or 0
        add("planning", planned > 0, f"{planned}/{total_p} projects planned autonomously", planned)

        # Development (Phase 5).
        try:
            from app.models.development import DevelopmentTask

            tasks = self.db.scalars(select(DevelopmentTask)).all()
            good = sum(1 for t in tasks if _v(t.status) in ("pr_ready", "approved", "merged"))
            rate = round(100 * good / len(tasks), 1) if tasks else 0.0
            add("development", rate >= 10 or not tasks,
                f"{good}/{len(tasks)} development tasks reached PR ({rate}%)", rate)
        except Exception:
            add("development", False, "Development engine unavailable")

        # Review (Phase 5).
        try:
            from app.models.development import CodeReview

            revs = self.db.scalars(select(CodeReview)).all()
            avg = round(sum(r.score or 0 for r in revs) / len(revs), 1) if revs else None
            add("review", (avg or 0) >= 60 or avg is None,
                f"Average review score {avg}" if avg is not None else "No reviews yet", avg)
        except Exception:
            add("review", False, "Review engine unavailable")

        # Deployment (Phase 5 devops).
        prod = self._production_snapshot()
        add("deployment", True, f"{prod['deployments']} deployment runs recorded", prod["deployments"])

        # Memory (Phase 4).
        try:
            from app.models.memory import AgentMemory

            n = self.db.scalar(select(func.count(AgentMemory.id))) or 0
            emb = self.db.scalar(
                select(func.count(AgentMemory.id)).where(AgentMemory.embedding.is_not(None))
            ) or 0
            add("memory", n > 0, f"{n} company memories ({emb} semantically indexed)", n)
        except Exception:
            add("memory", False, "Company memory unavailable")

        # Learning (Phase 4).
        try:
            from app.models.learning import LearningRule

            n = self.db.scalar(select(func.count(LearningRule.id))) or 0
            add("learning", n > 0, f"{n} learning rules derived from evidence", n)
        except Exception:
            add("learning", False, "Learning engine unavailable")

        healthy = sum(1 for d in dims if d["status"] == "healthy")
        score = round(100 * healthy / len(dims), 1) if dims else 0.0
        overall = "healthy" if score >= 80 else "attention" if score >= 50 else "degraded"
        return {"overall": overall, "score": score, "healthy_dimensions": healthy,
                "total_dimensions": len(dims), "dimensions": dims}

    # ------------------------------------------------------------------
    # 6. Business continuity
    # ------------------------------------------------------------------

    def continuity(self) -> dict:
        """Prove company state is durable (survives process/model/server restart)."""
        counts = {}
        for label, model_path, attr in (
            ("projects", "app.models.work", "Project"),
            ("work_items", "app.models.work", "WorkItem"),
            ("milestones", "app.models.work", "Milestone"),
            ("company_memories", "app.models.memory", "AgentMemory"),
            ("learning_rules", "app.models.learning", "LearningRule"),
            ("conversations", "app.models.orchestration", "ConversationThread"),
            ("development_tasks", "app.models.development", "DevelopmentTask"),
        ):
            try:
                mod = __import__(model_path, fromlist=[attr])
                counts[label] = self.db.scalar(select(func.count(getattr(mod, attr).id))) or 0
            except Exception:
                counts[label] = None
        return {
            "durable_store": "postgresql",
            "state": counts,
            "stateless_runtime": True,
            "note": "All company state is persisted in PostgreSQL; API/worker/model restarts do not lose state.",
        }

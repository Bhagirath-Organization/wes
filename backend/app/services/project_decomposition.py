"""Autonomous Project Decomposition (WP6, Phase 1).

Turns a Founder Project Intake (a business objective + deliverables + constraints)
into a real, reviewable plan built entirely from the EXISTING work schema:

    Intake -> Business Analysis (AI CEO) -> Epics (milestones) ->
    Sprints (project_sprints) -> Tasks (work_items) -> AI-employee assignment

The plan is produced in a ``decomposed`` state and MUST be Founder-approved before
any execution begins — decomposition never starts implementation (project.status
stays PLANNING). Assignment maps each task to a REAL seeded ``ai_employees`` row by
role, so tasks carry a genuine assignee (the bridge to WP7 collaboration).

Phase 1 (AI Executive Intelligence): analysis and task shaping are NO LONGER
deterministic. The AI CEO, AI CTO and AI Chief Architect reason for real through
the configured provider (see ``executive_reasoning``); epics and tasks come from
the Architect's design rather than a fixed lifecycle template. The public
contract (decompose / plan / approve_plan and the returned schema) is unchanged.
"""

from __future__ import annotations

import json
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.domain.ai_enums import AIDecisionAuthority
from app.domain.work_enums import (
    DependencyType,
    MilestoneStatus,
    Priority,
    ProjectStatus,
    SprintStatus,
    WorkStatus,
)
from app.models.ai import AIEmployee, AIRole
from app.models.work import Milestone, Project, ProjectSprint, WorkDependency, WorkItem


def _loads(v: str | None) -> list:
    if not v:
        return []
    try:
        data = json.loads(v)
        return data if isinstance(data, list) else [data]
    except (ValueError, TypeError):
        return [v]


class DecompositionService:
    def __init__(self, db: Session):
        self.db = db

    # -- AI employee lookup ------------------------------------------------

    def _employees_by_role(self) -> list[tuple[str, AIEmployee]]:
        rows = self.db.execute(
            select(AIRole.title, AIEmployee)
            .join(AIEmployee, AIEmployee.role_id == AIRole.id)
            .where(AIEmployee.is_deleted.is_(False))
        ).all()
        return [(t.lower(), e) for t, e in rows]

    def _find_employee(self, keyword: str) -> AIEmployee | None:
        pairs = self._employees_by_role()
        for title, emp in pairs:
            if keyword in title:
                return emp
        return None

    def _ceo(self) -> AIEmployee | None:
        # The executive with no manager is the AI CEO (business rule in the AI org).
        emp = self.db.scalar(
            select(AIEmployee)
            .where(
                AIEmployee.authority == AIDecisionAuthority.EXECUTIVE,
                AIEmployee.manager_id.is_(None),
                AIEmployee.is_deleted.is_(False),
            )
            .limit(1)
        )
        return emp or self.db.scalar(select(AIEmployee).limit(1))

    # -- business analysis (AI CEO) ---------------------------------------

    def _executive_pass(self, project: Project, domain_summary: str = "") -> dict:
        """Run the AI CEO -> CTO -> Architect reasoning chain for this project.

        Returns the combined executive decision. Raises rather than emitting a
        canned analysis if an executive cannot reason (Phase 1 rule).

        Phase B: ``domain_summary`` (the Business Understanding Report digest) is
        injected so every executive reasons WITH domain intelligence, not blind.
        """
        from app.services.executive_reasoning import ExecutiveReasoningService

        objective = project.business_objective or project.name
        deliverables = _loads(project.deliverables)
        constraints = _loads(project.constraints)
        context_bits = []
        if domain_summary:
            context_bits.append(f"BUSINESS UNDERSTANDING (understand before deciding):\n{domain_summary}")
        if project.business_problem:
            context_bits.append(f"Business problem: {project.business_problem}")
        if project.intake_description:
            context_bits.append(f"Details: {project.intake_description}")
        if deliverables:
            context_bits.append(f"Founder-stated deliverables: {', '.join(map(str, deliverables))}")
        if constraints:
            context_bits.append(f"Constraints: {', '.join(map(str, constraints))}")
        if project.acceptance_criteria:
            context_bits.append(f"Acceptance criteria: {project.acceptance_criteria}")
        if project.tech_stack:
            context_bits.append(f"Preferred stack: {project.tech_stack}")

        # Phase 2 owns task breakdown (the Planning Engine), so the executive pass
        # only needs the CEO analysis, the CTO strategy and the Architect's system
        # design + components. The Architect's Phase-1 epic/task JSON (a nested,
        # small-model-fragile structure) is NO LONGER required here — if it fails
        # to parse we still proceed with the design the Architect produced, and
        # the Planning Engine derives the tasks. Phase 1's own methods are unchanged.
        svc = ExecutiveReasoningService(self.db)
        ctx = "\n".join(context_bits)
        ceo = svc.ceo_analysis(objective, ctx)
        cto = svc.cto_strategy(objective, ceo)
        try:
            architect = svc.architect_design(objective, ceo, cto)
        except ValidationError:
            architect = self._architect_design_only(svc, objective, ceo, cto)
        return {"ceo": ceo, "cto": cto, "architect": architect}

    @staticmethod
    def _architect_design_only(svc, objective: str, ceo: dict, cto: dict) -> dict:
        """Architect system design + components WITHOUT the fragile nested epics.

        Used as a fallback when the Phase-1 architect call cannot return usable
        epics; Phase 2's Planning Engine performs the task breakdown regardless.
        """
        emp = svc._employee_for_role("CHIEF_ARCHITECT", "CTO")
        data = svc._reason(
            "AI Chief Architect",
            emp,
            "You are the AI Chief Architect. Describe the system design for this "
            "product. Reply with ONLY JSON: {\"design\":\"...\",\"components\":[\"...\"]}",
            f"Business objective: {objective}\nCEO vision: {ceo.get('vision')}\n"
            f"CTO strategy: {cto.get('strategy')}\nStack: {', '.join(cto.get('stack', []))}",
        )
        return {
            "architect": emp.name if emp else "AI Chief Architect",
            "design": str(data.get("design") or "").strip()[:2000],
            "components": [str(c).strip()[:400] for c in (data.get("components") or []) if str(c).strip()][:12],
            "epics": [],
        }

    def _analysis_record(self, executive: dict) -> dict:
        """Shape the executive decision into the stored business_analysis schema.

        Existing keys (analyst / vision / scope / risks / architecture_proposal)
        are preserved for backward compatibility; CTO and Architect detail is
        added alongside them.
        """
        ceo = executive["ceo"]
        cto = executive["cto"]
        arch = executive["architect"]
        return {
            "analyst": ceo.get("analyst"),
            "vision": ceo.get("vision"),
            "scope": ceo.get("scope", {}),
            "risks": ceo.get("risks", []),
            "success_criteria": ceo.get("success_criteria", []),
            # Backward-compatible field, now written by the AI Chief Architect.
            "architecture_proposal": arch.get("design"),
            "cto": {
                "strategist": cto.get("strategist"),
                "strategy": cto.get("strategy"),
                "stack": cto.get("stack", []),
                "key_decisions": cto.get("key_decisions", []),
                "technical_risks": cto.get("technical_risks", []),
            },
            "architect": {
                "architect": arch.get("architect"),
                "design": arch.get("design"),
                "components": arch.get("components", []),
            },
        }

    def _next_task_index(self, project: Project) -> int:
        n = (
            self.db.scalar(
                select(func.count(WorkItem.id)).where(WorkItem.project_id == project.id)
            )
            or 0
        )
        return n + 1

    def decompose(self, project_id: uuid.UUID) -> dict:
        project = self.db.get(Project, project_id)
        if project is None:
            raise NotFoundError(f"Project {project_id} not found")
        if project.plan_status == "approved":
            raise ValidationError("Project plan is already approved; decomposition is locked.")

        # WES-DEC-011: attribute every planning-chain provider call to this
        # mission so the envelope sees reasoning spend (read by the provider
        # orchestrator's metering).
        from app.services.mission_budget import mission_context

        with mission_context(project.id):
            return self._decompose_inner(project)

    def _decompose_inner(self, project: Project) -> dict:

        # Clear any prior (unapproved) decomposition so re-running is idempotent.
        for m in self.db.scalars(
            select(Milestone).where(Milestone.project_id == project.id)
        ).all():
            self.db.delete(m)
        for s in self.db.scalars(
            select(ProjectSprint).where(ProjectSprint.project_id == project.id)
        ).all():
            self.db.delete(s)
        for t in self.db.scalars(
            select(WorkItem).where(WorkItem.project_id == project.id)
        ).all():
            self.db.delete(t)
        self.db.flush()

        # Phase B: BUSINESS UNDERSTANDING FIRST. Before any executive reasoning,
        # architecture, planning or engineering, the Company Brain must understand
        # the business domain. Coding never happens before domain analysis.
        from app.services.domain_intelligence import DomainIntelligenceService

        objective = project.business_objective or project.name
        domain = DomainIntelligenceService(self.db)
        domain_context = []
        if project.business_problem:
            domain_context.append(f"Business problem: {project.business_problem}")
        if project.intake_description:
            domain_context.append(f"Details: {project.intake_description}")
        if project.acceptance_criteria:
            domain_context.append(f"Success criteria: {project.acceptance_criteria}")
        try:
            domain_report = domain.understand(
                objective, project_id=project.id, context="\n".join(domain_context)
            )
        except Exception:
            domain_report = None  # never block the pipeline on domain-model variance
        domain_summary = domain.summary_text(domain_report) if domain_report else ""

        # Phase 1: real executive reasoning (CEO -> CTO -> Architect), now informed
        # by the Business Understanding Report.
        executive = self._executive_pass(project, domain_summary)
        analysis = self._analysis_record(executive)
        if domain_report:
            analysis["domain_analysis"] = domain_report

        # Phase 3: executive collaboration — CEO/CTO/Architect debate the direction
        # BEFORE planning; the CEO's decision + agreed constraints influence the plan.
        from app.services.collaboration import CollaborationService
        from app.services.company_memory import CompanyMemoryService

        collab = CollaborationService(self.db)
        consensus = collab.executive_consensus(
            project, executive["ceo"], executive["cto"]
        )

        # Phase 2: autonomous planning engine — repository-aware, dependency-aware,
        # now constrained by the executives' agreed decisions (Phase 3 influence).
        from app.services.planning_engine import PlanningEngineService

        engine = PlanningEngineService(self.db)
        objective = project.business_objective or project.name

        # Phase 4: recall relevant company memory (similar past projects + learning
        # rules) so this plan reuses experience instead of starting from scratch.

        memory = CompanyMemoryService(self.db)
        memory_context = memory.planning_context(objective, exclude_project=project.id)

        blueprint = engine.build(
            objective, executive["ceo"], executive["cto"], executive["architect"],
            constraints=consensus.get("agreed_constraints"),
            memory_context=memory_context,
        )

        # Phase 3: review chain — Security + QA review the produced plan; may reject.
        plan_summary = "Milestones: " + "; ".join(
            m["name"] for m in blueprint["milestones"]
        ) + "\nTasks: " + "; ".join(t["title"] for t in blueprint["tasks"][:12])
        review = collab.review_chain(project, plan_summary)

        # Phase 4: capture this project's durable knowledge into company memory
        # (objective, decisions, architecture ADR, risks, findings) with real
        # embeddings + knowledge-graph links, and mine cross-project repetition
        # into evidence-based learning rules.
        memory_capture = memory.capture_project(
            project, executive, consensus, review, blueprint
        )
        # Phase B: every project improves company domain knowledge (industry,
        # workflows, rules, KPIs, compliance, automation) for future reuse.
        if domain_report:
            domain.remember_domain(project, domain_report)
        learned = memory.learn_from_repetition()
        analysis["repository_analysis"] = blueprint["repository_analysis"]
        analysis["gap_analysis"] = blueprint["gap_analysis"]
        analysis["risks_detailed"] = blueprint["risks"]
        project.business_analysis = json.dumps(analysis)
        project.plan_artifact = json.dumps(
            {
                "repository_analysis": blueprint["repository_analysis"],
                "gap_analysis": blueprint["gap_analysis"],
                "risks": blueprint["risks"],
                "graph": blueprint["graph"],
                "definition_of_done": blueprint["definition_of_done"],
                # Phase 3: the collaboration outcome that shaped this plan.
                "collaboration": {
                    "executive_consensus": consensus,
                    "plan_review": review,
                },
                # Phase 4: company memory reused (recall) + captured (write) + learned.
                "memory": {
                    "reused": memory_context,
                    "captured": memory_capture,
                    "learning_rules_created": learned,
                    "similar_projects": memory.similar_projects(project),
                },
            }
        )

        priority = project.priority if isinstance(project.priority, Priority) else Priority.MEDIUM
        task_idx = self._next_task_index(project)

        # -- milestones (reasoned, each with objective/deliverables/AC/DoD) ----
        milestones_by_key: dict[str, Milestone] = {}
        for m_spec in blueprint["milestones"]:
            milestone = Milestone(
                project_id=project.id,
                name=m_spec["name"],
                description=m_spec.get("business_objective") or m_spec["name"],
                status=MilestoneStatus.PENDING,
                business_objective=m_spec.get("business_objective") or None,
                deliverables=json.dumps(m_spec.get("deliverables") or []),
                acceptance_criteria=m_spec.get("acceptance_criteria") or None,
                definition_of_done=m_spec.get("definition_of_done") or None,
                review_trigger=m_spec.get("review_trigger") or None,
            )
            self.db.add(milestone)
            self.db.flush()
            milestones_by_key[m_spec["key"]] = milestone

        # -- sprints (reasoned count, capacity and exit criteria) --------------
        sprints_by_number: dict[int, ProjectSprint] = {}
        for s_spec in blueprint["sprints"]:
            sprint = ProjectSprint(
                project_id=project.id,
                sprint_number=s_spec["number"],
                goal=s_spec.get("objective") or f"Sprint {s_spec['number']}",
                status=SprintStatus.PLANNED,
                objective=s_spec.get("objective") or None,
                capacity_hours=s_spec.get("capacity_hours"),
                exit_criteria=s_spec.get("exit_criteria") or None,
                risk_level=s_spec.get("risk_level") or None,
            )
            self.db.add(sprint)
            self.db.flush()
            sprints_by_number[s_spec["number"]] = sprint

        # -- tasks in reasoned execution order, with intelligent allocation ----
        allocation = engine.allocate(blueprint["tasks"])
        tasks_by_key = {t["key"]: t for t in blueprint["tasks"]}
        order = blueprint["graph"]["execution_order"] or list(tasks_by_key)
        reviewer = self._find_employee("architect") or self._ceo()
        created_tasks: dict[str, WorkItem] = {}

        for key in order:
            spec = tasks_by_key.get(key)
            if spec is None:
                continue
            emp = allocation.get(key)
            milestone = milestones_by_key.get(spec.get("milestone_key") or "")
            sprint = sprints_by_number.get(spec.get("sprint_number"))
            task = WorkItem(
                task_code=f"{project.code}-T{task_idx:03d}",
                title=spec["title"],
                description=(
                    f"{spec['title']}"
                    + (f" (reuses: {', '.join(spec['reuses'])})" if spec.get("reuses") else "")
                ),
                # Measurable, task-specific acceptance criteria (Phase 2).
                acceptance_criteria=spec.get("acceptance_criteria")
                or (project.acceptance_criteria or None),
                definition_of_done=spec.get("definition_of_done") or None,
                priority=priority,
                status=WorkStatus.BACKLOG,
                estimated_hours=spec["hours"],
                project_id=project.id,
                sprint_id=sprint.id if sprint else None,
                milestone_id=milestone.id if milestone else None,
                assigned_ai_employee_id=emp.id if emp else None,
                reviewer_ai_employee_id=reviewer.id if reviewer else None,
            )
            self.db.add(task)
            self.db.flush()
            task_idx += 1
            created_tasks[key] = task

        # -- persist the REAL dependency graph (reuses work_dependencies) ------
        for key, spec in tasks_by_key.items():
            item = created_tasks.get(key)
            if item is None:
                continue
            for dep_key in spec.get("depends_on", []):
                parent = created_tasks.get(dep_key)
                if parent is None or parent.id == item.id:
                    continue
                self.db.add(
                    WorkDependency(
                        work_item_id=item.id,
                        depends_on_id=parent.id,
                        type=DependencyType.BLOCKS,
                    )
                )
        self.db.flush()

        # Decomposed, awaiting Founder approval. Implementation does NOT start.
        project.plan_status = "decomposed"
        project.status = ProjectStatus.PLANNING
        self.db.flush()

        return self.plan(project.id)

    def approve_plan(self, project_id: uuid.UUID, approved_by: str = "Founder") -> dict:
        project = self.db.get(Project, project_id)
        if project is None:
            raise NotFoundError(f"Project {project_id} not found")
        if project.plan_status != "decomposed":
            raise ValidationError(
                f"Project has no decomposed plan to approve (plan_status={project.plan_status})."
            )
        project.plan_status = "approved"
        self.db.flush()
        # Phase 4: Founder approval kicks off autonomous execution — enqueue a
        # durable project-execution job (turns tasks into dev workflows).
        from app.services.job_queue import JobQueue

        JobQueue(self.db).enqueue(
            "project_execution",
            {"project_id": str(project.id)},
            idempotency_key=f"project-exec:{project.id}",
        )
        return self.plan(project.id)

    def plan(self, project_id: uuid.UUID) -> dict:
        project = self.db.get(Project, project_id)
        if project is None:
            raise NotFoundError(f"Project {project_id} not found")
        from app.services.collaboration import CollaborationService
        from app.services.company_memory import CompanyMemoryService
        milestones = self.db.scalars(
            select(Milestone).where(Milestone.project_id == project.id).order_by(Milestone.name)
        ).all()
        sprints = self.db.scalars(
            select(ProjectSprint)
            .where(ProjectSprint.project_id == project.id)
            .order_by(ProjectSprint.sprint_number)
        ).all()
        tasks = self.db.scalars(
            select(WorkItem).where(WorkItem.project_id == project.id).order_by(WorkItem.task_code)
        ).all()
        emp_names = {
            e.id: e.name for e in self.db.scalars(select(AIEmployee)).all()
        }
        # Task-code -> code map for rendering dependency edges (Phase 2).
        code_by_id = {t.id: t.task_code for t in tasks}
        deps = self.db.scalars(
            select(WorkDependency).where(
                WorkDependency.work_item_id.in_([t.id for t in tasks] or [uuid.uuid4()])
            )
        ).all()
        dep_edges = [
            {
                "task": code_by_id.get(d.work_item_id),
                "depends_on": code_by_id.get(d.depends_on_id),
                "type": _v(d.type),
            }
            for d in deps
            if code_by_id.get(d.work_item_id) and code_by_id.get(d.depends_on_id)
        ]
        artifact = json.loads(project.plan_artifact) if project.plan_artifact else None
        return {
            "project": {
                "id": str(project.id),
                "code": project.code,
                "name": project.name,
                "business_objective": project.business_objective,
                "plan_status": project.plan_status,
                "status": project.status.value
                if hasattr(project.status, "value")
                else project.status,
            },
            "business_analysis": json.loads(project.business_analysis)
            if project.business_analysis
            else None,
            # Phase B: the Business Understanding Report (business-language),
            # surfaced first-class for the Founder. Produced BEFORE planning.
            "domain_analysis": (
                json.loads(project.business_analysis).get("domain_analysis")
                if project.business_analysis
                else None
            ),
            "epics": [
                {
                    "id": str(m.id),
                    "name": m.name,
                    "status": _v(m.status),
                    "business_objective": m.business_objective,
                    "deliverables": _loads(m.deliverables),
                    "acceptance_criteria": m.acceptance_criteria,
                    "definition_of_done": m.definition_of_done,
                    "review_trigger": m.review_trigger,
                }
                for m in milestones
            ],
            "sprints": [
                {
                    "sprint_number": s.sprint_number,
                    "goal": s.goal,
                    "status": _v(s.status),
                    "objective": s.objective,
                    "capacity_hours": s.capacity_hours,
                    "exit_criteria": s.exit_criteria,
                    "risk_level": s.risk_level,
                }
                for s in sprints
            ],
            "tasks": [
                {
                    "task_code": t.task_code,
                    "title": t.title,
                    "sprint_id": str(t.sprint_id) if t.sprint_id else None,
                    "milestone_id": str(t.milestone_id) if t.milestone_id else None,
                    "assignee": emp_names.get(t.assigned_ai_employee_id),
                    "reviewer": emp_names.get(t.reviewer_ai_employee_id),
                    "estimated_hours": t.estimated_hours,
                    "acceptance_criteria": t.acceptance_criteria,
                    "definition_of_done": t.definition_of_done,
                    "status": _v(t.status),
                }
                for t in tasks
            ],
            # Phase 2 additions (additive — existing keys above are unchanged).
            "dependencies": dep_edges,
            "repository_analysis": (artifact or {}).get("repository_analysis"),
            "gap_analysis": (artifact or {}).get("gap_analysis"),
            "risks": (artifact or {}).get("risks"),
            "graph": (artifact or {}).get("graph"),
            "definition_of_done": (artifact or {}).get("definition_of_done"),
            # Phase 3: collaboration outcome + full persistent conversation records.
            "collaboration": (artifact or {}).get("collaboration"),
            "conversations": CollaborationService(self.db).project_conversations(project.id),
            # Phase 4: company memory + knowledge graph for this project.
            "memory": (artifact or {}).get("memory"),
            "company_memory": CompanyMemoryService(self.db).project_memory(project.id),
            "totals": {
                "epics": len(milestones),
                "sprints": len(sprints),
                "tasks": len(tasks),
                "estimated_hours": sum(t.estimated_hours or 0 for t in tasks),
                "dependencies": len(dep_edges),
                "critical_path_hours": (artifact or {}).get("graph", {}).get("critical_path_hours"),
            },
        }


def _v(x) -> str:
    return x.value if hasattr(x, "value") else x

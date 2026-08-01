"""Autonomous Planning Engine (Phase 2).

Turns an executive decision (Phase 1: CEO -> CTO -> Architect) into a real,
company-grade delivery plan. Nothing here is templated: milestones, sprints,
tasks, dependencies and risks are all reasoned per project.

    Repository Analysis -> Gap Analysis -> Milestones & Sprints & Risks ->
    Task Breakdown (with dependencies) -> Graph computation -> Allocation

Two kinds of work are deliberately separated:

* **Reasoning** (what to build, what depends on what, what can be reused, what
  the risks are) is performed by the AI provider — never hardcoded.
* **Computation** (topological order, critical path, parallel waves, workload
  balancing) is deterministic graph maths over the reasoned dependencies. These
  are algorithms, not templates: the same maths applied to a different reasoned
  graph yields a different order, path and wave structure.

Repository awareness reuses the EXISTING Repository Intelligence
(``RepoAnalysisService``) so planning knows what already exists and avoids
redesigning or duplicating shipped functionality.
"""

from __future__ import annotations

import json
import uuid
from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.ai import AIEmployee, AIRole
from app.models.work import WorkItem

# Role keywords the Architect may assign work to, mapped to org role codes.
_ROLE_KEYWORDS = {
    "architect": ("CHIEF_ARCHITECT", "CTO"),
    "backend": ("BACKEND_ENGINEER",),
    "frontend": ("FRONTEND_ENGINEER",),
    "qa": ("QA_ENGINEER",),
    "security": ("SECURITY_ENGINEER",),
    "devops": ("DEVOPS_ENGINEER",),
    "writer": ("TECH_WRITER",),
    "docs": ("TECH_WRITER",),
    "ai": ("AI_ENGINEER",),
    "product": ("PRODUCT_MANAGER",),
    "design": ("UIUX_DESIGNER",),
}


def _s(value, limit: int = 600) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        value = "; ".join(str(v) for v in value)
    if isinstance(value, dict):
        value = json.dumps(value)
    return str(value).strip()[:limit]


def _slist(value, limit: int = 12, item_limit: int = 400) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (str, dict)):
        value = [value]
    out: list[str] = []
    for v in value:
        if isinstance(v, dict):
            v = v.get("name") or v.get("title") or v.get("description") or json.dumps(v)
        s = str(v).strip()
        if s:
            out.append(s[:item_limit])
    return out[:limit]


class PlanningEngineService:
    """Produces the full delivery plan for a project."""

    def __init__(self, db: Session):
        self.db = db
        from app.services.executive_reasoning import ExecutiveReasoningService

        # Reuse Phase 1 reasoning plumbing (provider resolution, structured JSON,
        # retry) without modifying it.
        self._exec = ExecutiveReasoningService(db)

    # -- reasoning helper ---------------------------------------------------

    def _reason(self, actor: str, role_codes: tuple[str, ...], instruction: str, question: str) -> dict:
        emp = self._exec._employee_for_role(*role_codes)
        return self._exec._reason(actor, emp, instruction, question)

    # -- 1. Repository awareness (reuses Repository Intelligence) -----------

    def repository_context(self) -> dict:
        """Summarise what ALREADY exists so planning can reuse, not rebuild."""
        from app.models.repository import Repository
        from app.services.repo_analysis import ArchitectureService, DependencyService

        repo = self.db.scalar(select(Repository).limit(1))
        if repo is None:
            return {"repository": None, "modules": [], "layers": [], "dependencies": [], "known": False}

        arch = ArchitectureService(self.db)
        deps_svc = DependencyService(self.db)
        try:
            modules = [_s(m.get("name"), 120) for m in arch.modules(repo.id)][:40]
        except Exception:
            modules = []
        try:
            layers = [_s(l.get("layer") or l.get("name"), 60) for l in arch.layers(repo.id)][:20]
        except Exception:
            layers = []
        try:
            deps = [_s(d.get("name"), 60) for d in deps_svc.external_dependencies(repo.id)][:30]
        except Exception:
            deps = []
        return {
            "repository": repo.name,
            "modules": [m for m in modules if m],
            "layers": [l for l in layers if l],
            "dependencies": [d for d in deps if d],
            "known": True,
        }

    def _repo_text(self, ctx: dict) -> str:
        if not ctx.get("known"):
            return "Existing repository: none registered (greenfield)."
        return (
            f"Existing repository '{ctx['repository']}'.\n"
            f"Existing modules: {', '.join(ctx['modules']) or 'none'}\n"
            f"Architecture layers: {', '.join(ctx['layers']) or 'none'}\n"
            f"Libraries already available: {', '.join(ctx['dependencies']) or 'none'}"
        )

    # -- 2. Gap analysis ----------------------------------------------------

    def gap_analysis(self, objective: str, repo_ctx: dict) -> dict:
        data = self._reason(
            "AI Chief Architect",
            ("CHIEF_ARCHITECT", "CTO"),
            "You are the AI Chief Architect doing a build-vs-reuse gap analysis. "
            "You MUST list at least one item in 'missing' (what must be built) and, "
            "when existing modules are listed, at least one 'reuse'. Reply with ONLY JSON:\n"
            '{"reuse":[{"component":"existing module to reuse","why":"reason"}],'
            '"missing":["capability that must be built for this product"],'
            '"duplication_risks":["existing thing we must NOT rebuild"]}',
            f"Objective: {objective}\n{self._repo_text(repo_ctx)}\n"
            "Identify what existing components should be reused and what is genuinely missing.",
        )
        reuse = []
        for r in (data.get("reuse") or [])[:12]:
            if isinstance(r, str):
                r = {"component": r, "why": ""}
            if isinstance(r, dict) and r.get("component"):
                reuse.append({"component": _s(r.get("component"), 200), "why": _s(r.get("why"), 300)})
        return {
            "reuse": reuse,
            "missing": _slist(data.get("missing")),
            "duplication_risks": _slist(data.get("duplication_risks")),
        }

    # -- 3. Milestones + sprints -------------------------------------------

    def milestones_and_sprints(self, objective: str, ceo: dict, cto: dict, gap: dict) -> dict:
        # Two focused calls (milestones, then sprints) rather than one large call.
        # A combined response is big enough to truncate on a small model, losing
        # the sprints; splitting keeps each response small enough to complete.
        m_data = self._reason(
            "AI Product Manager",
            ("PRODUCT_MANAGER", "CTO", "CHIEF_ARCHITECT"),
            "You are the AI Product Manager. Decide how many milestones THIS project "
            "needs (choose the number; at least 2). Reply with ONLY JSON:\n"
            '{"milestones":[{"key":"M1","name":"short name",'
            '"business_objective":"why it matters","deliverables":["deliverable"],'
            '"acceptance_criteria":"measurable pass condition",'
            '"definition_of_done":"when done","review_trigger":"what triggers review",'
            '"depends_on":[]}]}',
            f"Objective: {objective}\nVision: {_s(ceo.get('vision'))}\n"
            f"Strategy: {_s(cto.get('strategy'))}\n"
            f"Must build: {', '.join(gap.get('missing', []))}",
        )
        milestones = []
        for m in (m_data.get("milestones") or [])[:8]:
            if not isinstance(m, dict) or not m.get("name"):
                continue
            milestones.append(
                {
                    "key": _s(m.get("key") or m.get("name"), 40) or f"M{len(milestones)+1}",
                    "name": _s(m.get("name"), 180),
                    "business_objective": _s(m.get("business_objective"), 600),
                    "deliverables": _slist(m.get("deliverables")),
                    "acceptance_criteria": _s(m.get("acceptance_criteria"), 800),
                    "definition_of_done": _s(m.get("definition_of_done"), 800),
                    "review_trigger": _s(m.get("review_trigger"), 300),
                    "depends_on": _slist(m.get("depends_on"), 6, 40),
                }
            )

        m_keys = [m["key"] for m in milestones] or ["M1"]
        s_data = self._reason(
            "AI Product Manager",
            ("PRODUCT_MANAGER", "CTO", "CHIEF_ARCHITECT"),
            "You are the AI Product Manager sequencing sprints across the milestones. "
            "Decide the number of sprints (at least 1 per milestone is typical). "
            "Reply with ONLY JSON:\n"
            '{"sprints":[{"number":1,"objective":"sprint goal","capacity_hours":40,'
            '"exit_criteria":"exit condition","risk_level":"low|medium|high",'
            '"milestone_key":"M1"}]}',
            f"Objective: {objective}\nMilestones (by key): "
            + "; ".join(
                f"{m['key']}={m['name']}" for m in milestones
            )
            + f"\nStrategy: {_s(cto.get('strategy'))}",
        )
        sprints = []
        for s in (s_data.get("sprints") or [])[:12]:
            if not isinstance(s, dict):
                continue
            try:
                number = int(s.get("number") or len(sprints) + 1)
            except (TypeError, ValueError):
                number = len(sprints) + 1
            try:
                capacity = float(s.get("capacity_hours") or 40.0)
            except (TypeError, ValueError):
                capacity = 40.0
            sprints.append(
                {
                    "number": number,
                    "objective": _s(s.get("objective"), 600),
                    "capacity_hours": max(1.0, min(capacity, 400.0)),
                    "exit_criteria": _s(s.get("exit_criteria"), 600),
                    "risk_level": _s(s.get("risk_level"), 20).lower() or "medium",
                    "milestone_key": _s(s.get("milestone_key"), 40),
                }
            )
        return {"milestones": milestones, "sprints": sprints}

    # -- 4. Task breakdown with dependencies -------------------------------

    def task_breakdown(self, objective: str, cto: dict, plan: dict, gap: dict) -> list[dict]:
        m_keys = [m["key"] for m in plan["milestones"]]
        s_numbers = [s["number"] for s in plan["sprints"]]
        data = self._reason(
            "AI Chief Architect",
            ("CHIEF_ARCHITECT", "CTO"),
            "You are the AI Chief Architect breaking delivery into tasks. Each task "
            "needs MEASURABLE acceptance criteria and explicit dependencies on other "
            "task keys (use [] when a task can start immediately — those run in "
            "parallel). Reply with ONLY JSON:\n"
            '{"tasks":[{"key":"T1","title":"...","role":"backend",'
            '"hours":6,"milestone_key":"M1","sprint_number":1,'
            '"acceptance_criteria":"objectively verifiable statement",'
            '"definition_of_done":"...","depends_on":["T0"],"reuses":["existing component"]}]}\n'
            "Allowed roles: architect, backend, frontend, qa, security, devops, writer, ai, design.",
            f"Objective: {objective}\nStack: {', '.join(cto.get('stack', []))}\n"
            f"Milestones: {', '.join(m_keys)}\nSprints: {s_numbers}\n"
            f"Must build: {', '.join(gap.get('missing', []))}\n"
            f"Reuse existing (do NOT rebuild): "
            f"{', '.join(r['component'] for r in gap.get('reuse', []))}\n"
            "Order tasks so dependent work follows what it needs.",
        )
        tasks = []
        seen = set()
        for t in (data.get("tasks") or [])[:40]:
            if not isinstance(t, dict) or not t.get("title"):
                continue
            key = _s(t.get("key"), 30) or f"T{len(tasks)+1}"
            if key in seen:
                key = f"{key}-{len(tasks)+1}"
            seen.add(key)
            try:
                hours = float(t.get("hours") or 4.0)
            except (TypeError, ValueError):
                hours = 4.0
            role = _s(t.get("role"), 30).lower() or "backend"
            tasks.append(
                {
                    "key": key,
                    "title": _s(t.get("title"), 200),
                    "role": role,
                    "hours": max(0.5, min(hours, 80.0)),
                    "milestone_key": _s(t.get("milestone_key"), 40),
                    "sprint_number": t.get("sprint_number"),
                    "acceptance_criteria": _s(t.get("acceptance_criteria"), 800),
                    "definition_of_done": _s(t.get("definition_of_done"), 600),
                    "depends_on": [k for k in _slist(t.get("depends_on"), 8, 30) if k != key],
                    "reuses": _slist(t.get("reuses"), 6),
                }
            )
        # Drop dependencies pointing at unknown keys (model hallucination guard).
        valid = {t["key"] for t in tasks}
        for t in tasks:
            t["depends_on"] = [d for d in t["depends_on"] if d in valid]
        return tasks

    # -- 5. Risk analysis ---------------------------------------------------

    def risk_analysis(self, objective: str, cto: dict, gap: dict) -> list[dict]:
        data = self._reason(
            "AI Security Engineer",
            ("SECURITY_ENGINEER", "CTO", "CHIEF_ARCHITECT"),
            "You are assessing delivery risk across architecture, security, "
            "performance, data/migration, integration, deployment and business. "
            "Reply with ONLY JSON:\n"
            '{"risks":[{"title":"...","category":"security","probability":"low|medium|high",'
            '"impact":"low|medium|high","mitigation":"...","owner_role":"security"}]}',
            f"Objective: {objective}\nStack: {', '.join(cto.get('stack', []))}\n"
            f"Known technical risks: {', '.join(cto.get('technical_risks', []))}\n"
            f"New capabilities: {', '.join(gap.get('missing', []))}",
        )
        risks = []
        for r in (data.get("risks") or [])[:15]:
            if not isinstance(r, dict) or not r.get("title"):
                continue
            risks.append(
                {
                    "title": _s(r.get("title"), 300),
                    "category": _s(r.get("category"), 40).lower() or "delivery",
                    "probability": _s(r.get("probability"), 20).lower() or "medium",
                    "impact": _s(r.get("impact"), 20).lower() or "medium",
                    "mitigation": _s(r.get("mitigation"), 600),
                    "owner_role": _s(r.get("owner_role"), 40).lower() or "architect",
                }
            )
        return risks

    # -- 6. Deterministic graph computation --------------------------------

    @staticmethod
    def compute_graph(tasks: list[dict]) -> dict:
        """Topological order, parallel waves and critical path.

        Pure maths over the REASONED dependency edges — not a template. Cycles
        are broken defensively so a hallucinated loop cannot hang planning.
        """
        by_key = {t["key"]: t for t in tasks}
        deps = {t["key"]: [d for d in t["depends_on"] if d in by_key] for t in tasks}
        dependents: dict[str, list[str]] = defaultdict(list)
        for k, ds in deps.items():
            for d in ds:
                dependents[d].append(k)

        # Kahn topological sort -> execution order + parallel waves.
        indegree = {k: len(ds) for k, ds in deps.items()}
        waves: list[list[str]] = []
        remaining = dict(indegree)
        while remaining:
            ready = sorted([k for k, v in remaining.items() if v == 0])
            if not ready:  # cycle -> break it deterministically
                ready = [sorted(remaining)[0]]
            waves.append(ready)
            for k in ready:
                remaining.pop(k, None)
                for child in dependents.get(k, []):
                    if child in remaining:
                        remaining[child] -= 1

        order = [k for wave in waves for k in wave]

        # Longest weighted path (critical path) over the DAG in topological order.
        finish: dict[str, float] = {}
        prev: dict[str, str | None] = {}
        for k in order:
            best_pred, best_finish = None, 0.0
            for d in deps.get(k, []):
                if finish.get(d, 0.0) > best_finish:
                    best_finish, best_pred = finish[d], d
            finish[k] = best_finish + float(by_key[k]["hours"])
            prev[k] = best_pred
        critical_path: list[str] = []
        if finish:
            node = max(finish, key=lambda k: finish[k])
            duration = finish[node]
            while node:
                critical_path.append(node)
                node = prev.get(node)
            critical_path.reverse()
        else:
            duration = 0.0

        blocking = {k: sorted(v) for k, v in dependents.items() if v}
        return {
            "execution_order": order,
            "parallel_waves": waves,
            "critical_path": critical_path,
            "critical_path_hours": round(duration, 1),
            "blocking": blocking,
            "edges": [{"task": k, "depends_on": d} for k, ds in deps.items() for d in ds],
            "total_hours": round(sum(float(t["hours"]) for t in tasks), 1),
            "max_parallelism": max((len(w) for w in waves), default=0),
        }

    # -- 7. Resource allocation --------------------------------------------

    def allocate(self, tasks: list[dict]) -> dict[str, AIEmployee]:
        """Assign each task by role skill, balancing existing + planned workload."""
        rows = self.db.execute(
            select(AIRole.code, AIEmployee)
            .join(AIEmployee, AIEmployee.role_id == AIRole.id)
            .where(AIEmployee.is_deleted.is_(False))
        ).all()
        by_code: dict[str, list[AIEmployee]] = defaultdict(list)
        for code, emp in rows:
            by_code[str(code).upper()].append(emp)

        # Current workload = open work items already assigned to each employee.
        counts = dict(
            self.db.execute(
                select(WorkItem.assigned_ai_employee_id, func.count(WorkItem.id)).group_by(
                    WorkItem.assigned_ai_employee_id
                )
            ).all()
        )
        load: dict[uuid.UUID, int] = {e.id: int(counts.get(e.id, 0) or 0) for _, e in rows}

        assignment: dict[str, AIEmployee] = {}
        for task in tasks:
            codes = _ROLE_KEYWORDS.get(task["role"], ("BACKEND_ENGINEER",))
            pool: list[AIEmployee] = []
            for code in codes:
                pool.extend(by_code.get(code, []))
            if not pool:  # unknown role -> anyone, least loaded
                pool = [e for _, e in rows]
            if not pool:
                continue
            chosen = min(pool, key=lambda e: (load.get(e.id, 0), str(e.id)))
            load[chosen.id] = load.get(chosen.id, 0) + 1  # balance within this plan
            assignment[task["key"]] = chosen
        return assignment

    # -- full plan ----------------------------------------------------------

    def build(
        self, objective: str, ceo: dict, cto: dict, architect: dict,
        constraints: list[str] | None = None,
        memory_context: str = "",
    ) -> dict:
        """Run the whole planning pipeline for one project.

        ``constraints`` (Phase 3): binding decisions the AI executives AGREED on
        during collaboration. When present they are woven into the objective so
        the reasoned plan respects them — this is how conversations influence
        planning. Backward compatible: omitted ⇒ identical Phase 2 behaviour.
        """
        if constraints:
            objective = (
                f"{objective}\nAgreed constraints from executive collaboration "
                f"(MUST be respected): {'; '.join(constraints)}"
            )
        # Phase 4: reuse company memory — inject knowledge from similar past
        # projects and known mistakes to avoid, so planning builds on experience.
        if memory_context:
            objective = f"{objective}\n\nCOMPANY MEMORY (reuse, don't redo):\n{memory_context}"
        repo_ctx = self.repository_context()
        gap = self.gap_analysis(objective, repo_ctx)
        ms = self.milestones_and_sprints(objective, ceo, cto, gap)
        tasks = self.task_breakdown(objective, cto, ms, gap)
        risks = self.risk_analysis(objective, cto, gap)
        graph = self.compute_graph(tasks)
        return {
            "repository_analysis": repo_ctx,
            "gap_analysis": gap,
            "milestones": ms["milestones"],
            "sprints": ms["sprints"],
            "tasks": tasks,
            "risks": risks,
            "graph": graph,
            "definition_of_done": {
                "project": (
                    "All milestones meet their Definition of Done, acceptance criteria "
                    "are demonstrably satisfied, quality gates pass and the Founder has "
                    "approved the release."
                )
            },
        }

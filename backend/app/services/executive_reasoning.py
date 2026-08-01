"""Executive AI reasoning (Phase 1 — AI Executive Intelligence).

Replaces the deterministic, templated executive decisions in
``project_decomposition`` with GENUINE reasoning performed by the configured AI
provider, through the existing Provider Abstraction Layer.

Three executives reason in sequence, each seeing the prior one's output — this is
the AI Decision Hierarchy from Blueprint Volume 05 expressed in code:

    AI CEO        -> business reasoning   (vision, scope, risks, success criteria)
    AI CTO        -> technical strategy   (approach, stack, decisions, tech risks)
    AI Architect  -> system design        (components + epics + the tasks per epic)

Each actor resolves its OWN provider via ``provider_for_employee`` so the AI-employee
-> provider mapping is honoured. There is no template fallback: if an executive
cannot produce a usable decision, the caller fails loudly rather than emitting a
canned plan (no fixed responses, no deterministic planning).
"""

from __future__ import annotations

import json
import re

from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError
from app.providers import ExecutionRequest, Message

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)

# Executive decisions need room for the model's reasoning trace *and* the JSON
# answer that follows it.
_REASONING_MAX_TOKENS = 6144


def _strip_thinking(text: str) -> str:
    """Remove reasoning traces (paired, or an implicit-open </think>)."""
    text = _THINK_RE.sub("", text)
    if "</think>" in text:
        text = text.rsplit("</think>", 1)[1]
    return text.strip()


def _extract_json(text: str) -> dict:
    """Return the first well-formed JSON object in the model's answer.

    Small models often narrate before answering; scan for balanced ``{...}``
    candidates and return the first that parses.
    """
    cleaned = _strip_thinking(text)
    cleaned = re.sub(r"^```[a-zA-Z0-9_+-]*[ \t]*\n", "", cleaned)
    cleaned = re.sub(r"\n```[ \t]*$", "", cleaned)

    # 1. The whole answer (fast path when the model returns pure JSON).
    try:
        obj = json.loads(cleaned)
        if isinstance(obj, dict):
            return obj
    except ValueError:
        pass

    # 2. The OUTERMOST object: first '{' to its matching '}'. This must be tried
    #    before any inner scan, otherwise a nested element (e.g. a single
    #    milestone {"key":...}) would be mistaken for the root object.
    first = cleaned.find("{")
    if first != -1:
        depth = 0
        for i in range(first, len(cleaned)):
            if cleaned[i] == "{":
                depth += 1
            elif cleaned[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        obj = json.loads(cleaned[first : i + 1])
                        if isinstance(obj, dict):
                            return obj
                    except ValueError:
                        pass
                    break
        # 2b. Truncated root object (generation hit the token cap mid-JSON):
        #     close the open braces/brackets and retry so partial-but-valid
        #     content is still recovered.
        tail = cleaned[first:]
        repaired = _close_json(tail)
        if repaired is not None and isinstance(repaired, dict):
            return repaired

    # 3. Last resort: the first balanced object anywhere.
    for start in (i for i, ch in enumerate(cleaned) if ch == "{"):
        depth = 0
        for i in range(start, len(cleaned)):
            if cleaned[i] == "{":
                depth += 1
            elif cleaned[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        obj = json.loads(cleaned[start : i + 1])
                        if isinstance(obj, dict):
                            return obj
                    except ValueError:
                        break
                    break
    raise ValueError(f"no JSON object in model output (len={len(cleaned)})")


def _close_json(text: str):
    """Best-effort repair of a JSON object truncated by the token cap.

    Trims to the last complete value, then closes any still-open brackets. Returns
    a dict on success, else None. This never invents data — it only recovers the
    prefix the model already emitted.
    """
    # Cut at the last COMPLETE structural close (never mid-string), dropping any
    # partial trailing value.
    cut = max(text.rfind("}"), text.rfind("]"))
    if cut < 0:
        return None
    candidate = text[: cut + 1]
    # Balance quotes are assumed closed at cut; balance braces/brackets by scanning.
    stack: list[str] = []
    in_str = False
    esc = False
    for ch in candidate:
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch in "{[":
            stack.append(ch)
        elif ch == "}":
            if stack and stack[-1] == "{":
                stack.pop()
        elif ch == "]":
            if stack and stack[-1] == "[":
                stack.pop()
    closing = "".join("}" if c == "{" else "]" for c in reversed(stack))
    candidate = candidate.rstrip().rstrip(",") + closing
    try:
        obj = json.loads(candidate)
        return obj if isinstance(obj, dict) else None
    except ValueError:
        return None


def _as_list(value, limit: int = 12) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    out = []
    for v in value:
        if isinstance(v, dict):
            v = v.get("name") or v.get("title") or json.dumps(v)
        s = str(v).strip()
        if s:
            out.append(s[:400])
    return out[:limit]


class ExecutiveReasoningService:
    """Runs the three executive actors against the configured AI provider."""

    def __init__(self, db: Session):
        self.db = db

    # -- provider plumbing -------------------------------------------------

    def _employee_for_role(self, *role_codes: str):
        from app.models.ai import AIEmployee, AIRole
        from sqlalchemy import select

        rows = self.db.execute(
            select(AIRole.code, AIEmployee)
            .join(AIEmployee, AIEmployee.role_id == AIRole.id)
            .where(AIEmployee.is_deleted.is_(False))
        ).all()
        by_code = {str(c).upper(): e for c, e in rows}
        for code in role_codes:
            emp = by_code.get(code.upper())
            if emp is not None:
                return emp
        return None

    # Executive actor -> orchestrator task type (Phase C). Executives declare WHAT
    # they are doing; the Company Brain's orchestrator decides WHICH provider runs it.
    _ACTOR_TASK = {
        "AI CEO": "business_strategy",
        "AI Business Analyst": "domain_understanding",
        "AI Business Architect": "domain_understanding",
        "AI CTO": "architecture",
        "AI Chief Architect": "architecture",
        "AI Security Engineer": "security",
        "AI QA Engineer": "testing",
        "AI Performance Reviewer": "review",
        "AI Backend Engineer (debug)": "coding",
    }

    def _reason(self, actor: str, employee, instruction: str, question: str) -> dict:
        """One executive decision. Provider selection + fallback are owned by the
        Company Brain's AI Provider Orchestrator (Phase C); this method only decides
        WHAT to ask and parses the JSON. No provider-specific logic lives here."""
        from app.services.providers_service import ProviderService
        from app.services.provider_orchestrator import AIProviderOrchestrator

        providers = ProviderService(self.db)
        orchestrator = AIProviderOrchestrator(self.db)
        # Role mapping remains a *hint*; the orchestrator may route elsewhere by
        # capability/health/learning, and will fall back automatically on failure.
        prefer = None
        try:
            prefer = (providers.provider_for_employee(employee).name
                      if employee is not None else None)
        except Exception:
            prefer = None
        task_type = self._ACTOR_TASK.get(actor, "reasoning")

        last_error: Exception | None = None
        for attempt in range(2):
            prefix = (
                "/no_think\n"
                if attempt == 0
                else "/no_think\nRespond with the JSON object ONLY. No reasoning, no prose.\n"
            )
            request = ExecutionRequest(
                messages=[
                    Message("system", instruction),
                    Message("user", f"{prefix}{question}"),
                ],
                max_tokens=_REASONING_MAX_TOKENS,
                metadata={"role": actor, "task": "executive-reasoning", "format": "json"},
            )
            try:
                result, _used = orchestrator.execute(
                    request, task_type=task_type, prefer=prefer
                )
            except Exception as exc:  # every provider failed / none available
                raise ValidationError(
                    f"{actor}: reasoning could not be executed by any provider: {exc}"
                ) from exc
            try:
                return _extract_json(result.output or "")
            except ValueError as exc:
                last_error = exc
        raise ValidationError(
            f"{actor} reasoning produced no parseable decision: {last_error}. "
            "Refusing to emit a templated plan."
        ) from last_error

    # -- AI CEO ------------------------------------------------------------

    def ceo_analysis(self, objective: str, context: str) -> dict:
        emp = self._employee_for_role("CEO")
        # Company Brain: gather what the company already knows (memory, past
        # mistakes, repository, Blueprint) and reason WITH it (Phase A). One call,
        # richer output — legacy keys preserved, structured reasoning added.
        from app.services.company_brain import CompanyBrain, REASONING_SCHEMA

        brain = CompanyBrain(self.db)
        intel = brain.intelligence(objective)
        data = self._reason(
            "AI CEO",
            emp,
            "You are the AI CEO of a software studio. Analyse the business objective "
            "USING the company intelligence provided (Blueprint, similar past projects, "
            "mistakes to avoid, existing repository). Consider alternatives before "
            "recommending. Reply with ONLY a JSON object, no prose:\n"
            '{"vision":"...","in_scope":["..."],"out_of_scope":["..."],'
            '"risks":["..."],"success_criteria":["..."],' + REASONING_SCHEMA[1:],
            f"Business objective: {objective}\n\nCOMPANY INTELLIGENCE:\n"
            f"{brain.intel_text(intel)}\n{context}",
        )
        analysis = {
            "vision": str(data.get("vision") or "").strip()[:1000],
            "scope": {
                "in_scope": _as_list(data.get("in_scope")),
                "out_of_scope": _as_list(data.get("out_of_scope")),
            },
            "risks": _as_list(data.get("risks")),
            "success_criteria": _as_list(data.get("success_criteria")),
        }
        if not analysis["vision"]:
            raise ValidationError("AI CEO returned no vision; refusing templated fallback.")
        analysis["analyst"] = emp.name if emp else "AI CEO"
        analysis["reasoning"] = brain.normalize(data, role="CEO", intel=intel,
                                                analyst=analysis["analyst"])
        return analysis

    # -- AI CTO ------------------------------------------------------------

    def cto_strategy(self, objective: str, ceo: dict) -> dict:
        emp = self._employee_for_role("CTO", "CHIEF_ARCHITECT")
        # Company Brain: reason about technology WITH repository intelligence (reuse
        # existing modules), Blueprint, and past technical mistakes (Phase A).
        from app.services.company_brain import CompanyBrain, REASONING_SCHEMA

        brain = CompanyBrain(self.db)
        intel = brain.intelligence(objective)
        data = self._reason(
            "AI CTO",
            emp,
            "You are the AI CTO. Given the business analysis and the company "
            "intelligence provided (existing repository modules to REUSE, Blueprint, "
            "past technical mistakes), decide the technical strategy. Consider "
            "alternatives. Reply with ONLY a JSON object, no prose:\n"
            '{"strategy":"...","stack":["..."],"key_decisions":["..."],'
            '"technical_risks":["..."],' + REASONING_SCHEMA[1:],
            f"Business objective: {objective}\n"
            f"CEO vision: {ceo.get('vision')}\n"
            f"In scope: {', '.join(ceo.get('scope', {}).get('in_scope', []))}\n\n"
            f"COMPANY INTELLIGENCE:\n{brain.intel_text(intel)}",
        )
        strategy = {
            "strategist": emp.name if emp else "AI CTO",
            "strategy": str(data.get("strategy") or "").strip()[:1500],
            "stack": _as_list(data.get("stack")),
            "key_decisions": _as_list(data.get("key_decisions")),
            "technical_risks": _as_list(data.get("technical_risks")),
        }
        if not strategy["strategy"]:
            raise ValidationError("AI CTO returned no strategy; refusing templated fallback.")
        strategy["reasoning"] = brain.normalize(data, role="CTO", intel=intel,
                                                analyst=strategy["strategist"])
        return strategy

    # -- AI Chief Architect -------------------------------------------------

    def architect_design(self, objective: str, ceo: dict, cto: dict) -> dict:
        emp = self._employee_for_role("CHIEF_ARCHITECT", "CTO")
        # Company Brain: design WITH repository intelligence so the architect reuses
        # existing modules/patterns instead of duplicating them, stays consistent
        # with the architecture layers, and cites the Blueprint (Phase A).
        from app.services.company_brain import CompanyBrain

        brain = CompanyBrain(self.db)
        intel = brain.intelligence(objective)
        data = self._reason(
            "AI Chief Architect",
            emp,
            "You are the AI Chief Architect. Using the company intelligence provided "
            "(EXISTING repository modules to REUSE, architecture layers, Blueprint, "
            "past mistakes), design the system and break it into delivery epics with "
            "concrete tasks. Reply with ONLY a JSON object, no prose:\n"
            '{"design":"...","components":["..."],"reuse":["existing modules reused"],'
            '"technical_debt":["..."],"alternatives":["..."],"confidence":0.0,'
            '"epics":[{"name":"...",'
            '"tasks":[{"title":"...","role":"backend","hours":6}]}]}\n'
            'Allowed role values: architect, backend, frontend, qa, writer, devops, security.\n'
            "Give 2-4 epics, each with 2-5 tasks that are specific to THIS product.",
            f"Business objective: {objective}\n"
            f"CEO vision: {ceo.get('vision')}\n"
            f"CTO strategy: {cto.get('strategy')}\n"
            f"Stack: {', '.join(cto.get('stack', []))}\n\n"
            f"COMPANY INTELLIGENCE:\n{brain.intel_text(intel)}",
        )

        epics: list[dict] = []
        for raw_epic in (data.get("epics") or [])[:6]:
            if isinstance(raw_epic, str):
                raw_epic = {"name": raw_epic, "tasks": []}
            if not isinstance(raw_epic, dict):
                continue
            name = str(raw_epic.get("name") or "").strip()[:180]
            if not name:
                continue
            tasks: list[dict] = []
            for raw_task in (raw_epic.get("tasks") or [])[:8]:
                if isinstance(raw_task, str):
                    raw_task = {"title": raw_task}
                if not isinstance(raw_task, dict):
                    continue
                title = str(raw_task.get("title") or "").strip()[:200]
                if not title:
                    continue
                try:
                    hours = float(raw_task.get("hours") or 4.0)
                except (TypeError, ValueError):
                    hours = 4.0
                tasks.append(
                    {
                        "title": title,
                        "role": str(raw_task.get("role") or "backend").strip().lower()[:40],
                        "hours": max(0.5, min(hours, 80.0)),
                    }
                )
            if tasks:
                epics.append({"name": name, "tasks": tasks})

        if not epics:
            raise ValidationError(
                "AI Chief Architect returned no usable epics/tasks; "
                "refusing to fall back to the lifecycle template."
            )
        result = {
            "architect": emp.name if emp else "AI Chief Architect",
            "design": str(data.get("design") or "").strip()[:2000],
            "components": _as_list(data.get("components")),
            "reuse": _as_list(data.get("reuse")),
            "technical_debt": _as_list(data.get("technical_debt")),
            "epics": epics,
        }
        result["reasoning"] = brain.normalize(data, role="CHIEF_ARCHITECT", intel=intel,
                                              analyst=result["architect"])
        return result

    # -- full executive pass -----------------------------------------------

    def executive_plan(self, objective: str, context: str = "") -> dict:
        """CEO -> CTO -> Architect, each informed by the previous decision."""
        ceo = self.ceo_analysis(objective, context)
        cto = self.cto_strategy(objective, ceo)
        architect = self.architect_design(objective, ceo, cto)
        return {"ceo": ceo, "cto": cto, "architect": architect}

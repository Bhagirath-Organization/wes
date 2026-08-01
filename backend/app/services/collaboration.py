"""AI Workforce Collaboration (Phase 3).

Turns the sequential CEO -> CTO -> Architect -> Planning pipeline into a real
collaborative company: employees ask questions, challenge assumptions, review
each other's work, approve, reject and escalate. Every turn is a genuine
reasoning call through the configured provider (no scripted dialogue) and is
stored as a persistent company record.

Reuses the EXISTING conversation store — ``ConversationThread`` (one per project
collaboration) and ``ExecutionMessage`` (one per turn, now tagged with the
speaker employee and the collaboration type) — so nothing new is invented for
persistence and the existing conversation APIs keep working.

Two collaborations are provided, both bounded so they run on CPU-only inference:

* ``executive_consensus`` — CEO ↔ CTO ↔ Architect debate the direction BEFORE
  planning. The CEO decides; agreed constraints/concerns flow into the Planning
  Engine (so conversations influence planning).
* ``review_chain`` — Security and QA review the produced plan AFTER planning and
  may reject/escalate.

No turn is hardcoded: whether an employee agrees, challenges or rejects is the
model's decision, so different projects produce different discussions.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.orchestration_enums import CollaborationType, MessageRole
from app.models.ai import AIEmployee, AIRole
from app.models.orchestration import ConversationThread, ExecutionMessage


def _s(v, limit: int = 1200) -> str:
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        v = "; ".join(str(x) for x in v)
    return str(v).strip()[:limit]


def _slist(v, n=10):
    if v is None:
        return []
    if isinstance(v, str):
        v = [v]
    return [str(x).strip()[:300] for x in v if str(x).strip()][:n]


class CollaborationService:
    def __init__(self, db: Session):
        self.db = db
        from app.services.executive_reasoning import ExecutiveReasoningService

        self._exec = ExecutiveReasoningService(db)  # reuse provider plumbing
        self._seq = 0

    # -- persistence (reuses ConversationThread + ExecutionMessage) ---------

    def open_thread(self, project_id: uuid.UUID, title: str, kind: str) -> ConversationThread:
        thread = ConversationThread(
            title=title[:200], status="open", project_id=project_id, kind=kind
        )
        self.db.add(thread)
        self.db.flush()
        self._seq = 0
        return thread

    def _emp(self, *role_codes: str) -> AIEmployee | None:
        rows = self.db.execute(
            select(AIRole.code, AIRole.title, AIEmployee)
            .join(AIEmployee, AIEmployee.role_id == AIRole.id)
            .where(AIEmployee.is_deleted.is_(False))
        ).all()
        by_code = {str(c).upper(): (t, e) for c, t, e in rows}
        for code in role_codes:
            if code.upper() in by_code:
                return by_code[code.upper()][1]
        return None

    def _role_title(self, emp: AIEmployee | None) -> str:
        if emp is None or emp.role_id is None:
            return "AI Employee"
        role = self.db.get(AIRole, emp.role_id)
        return role.title if role else "AI Employee"

    def say(
        self,
        thread: ConversationThread,
        speaker: AIEmployee | None,
        msg_type: CollaborationType,
        content: str,
        to: AIEmployee | None = None,
    ) -> ExecutionMessage:
        msg = ExecutionMessage(
            thread_id=thread.id,
            role=MessageRole.ASSISTANT,
            content=_s(content, 4000),
            sequence=self._seq,
            speaker_employee_id=speaker.id if speaker else None,
            to_employee_id=to.id if to else None,
            message_type=msg_type.value,
            speaker_role=self._role_title(speaker),
        )
        self.db.add(msg)
        self.db.flush()
        self._seq += 1
        return msg

    # -- one reasoned turn --------------------------------------------------

    def _turn(self, actor_label: str, role_codes: tuple[str, ...], instruction: str, prompt: str) -> dict:
        emp = self._emp(*role_codes)
        data = self._exec._reason(actor_label, emp, instruction, prompt)
        return {"employee": emp, "role_title": self._role_title(emp), "data": data}

    # -- executive consensus (BEFORE planning) ------------------------------

    def executive_consensus(self, project, ceo: dict, cto: dict) -> dict:
        """CEO ↔ CTO ↔ Architect debate the direction; CEO decides.

        Returns a consensus dict whose ``constraints``/``concerns`` feed planning.
        Persists every turn (question / answer / review / decision / escalation).
        """
        objective = project.business_objective or project.name
        thread = self.open_thread(
            project.id, f"Executive consensus — {project.name}", "executive_consensus"
        )
        base = (
            f"Objective: {objective}\n"
            f"CEO vision: {_s(ceo.get('vision'))}\n"
            f"CTO strategy: {_s(cto.get('strategy'))}\n"
            f"CTO stack: {', '.join(cto.get('stack', []))}\n"
            f"CTO technical risks: {', '.join(cto.get('technical_risks', []))}"
        )

        # 1. CEO raises a real strategic question/concern to the CTO.
        t1 = self._turn(
            "AI CEO", ("CEO",),
            "You are the AI CEO. You do NOT blindly accept the CTO's strategy — you "
            "interrogate it for business risk, cost and time-to-value. Ask the CTO ONE "
            "pointed question or raise ONE concern about delivering this objective. "
            "Reply with ONLY JSON: {\"question\":\"...\",\"concern\":\"...\"}",
            base,
        )
        ceo_emp = t1["employee"]
        cto_emp = self._emp("CTO", "CHIEF_ARCHITECT")
        arch_emp = self._emp("CHIEF_ARCHITECT", "CTO")
        q = _s(t1["data"].get("question") or t1["data"].get("concern"), 1000)
        self.say(thread, ceo_emp, CollaborationType.QUESTION, q, to=cto_emp)

        # 2. CTO responds — may push back / clarify / propose a change.
        t2 = self._turn(
            "AI CTO", ("CTO", "CHIEF_ARCHITECT"),
            "You are the AI CTO. Answer the CEO honestly. You MAY disagree, request "
            "clarification, or propose a change to protect technical quality — do not "
            "just agree. Reply with ONLY JSON: {\"answer\":\"...\",\"agree\":true,"
            "\"pushback\":\"...\",\"proposed_constraints\":[\"...\"]}",
            f"{base}\nCEO asked: {q}",
        )
        cto_agree = bool(t2["data"].get("agree", True))
        cto_answer = _s(t2["data"].get("answer"), 1500)
        pushback = _s(t2["data"].get("pushback"), 1000)
        proposed = _slist(t2["data"].get("proposed_constraints"))
        self.say(
            thread, cto_emp,
            CollaborationType.ANSWER if cto_agree else CollaborationType.CONCERN,
            cto_answer + (f"\nPushback: {pushback}" if pushback else ""),
            to=ceo_emp,
        )

        # 3. Architect reviews the exchange and takes a position (may challenge).
        t3 = self._turn(
            "AI Chief Architect", ("CHIEF_ARCHITECT", "CTO"),
            "You are the AI Chief Architect. Review the CEO/CTO exchange. Endorse or "
            "CHALLENGE the technical direction and add any architectural constraint. "
            "Reply with ONLY JSON: {\"position\":\"endorse|challenge\",\"reason\":\"...\","
            "\"architectural_constraints\":[\"...\"]}",
            f"{base}\nCTO answer: {cto_answer}\nCTO pushback: {pushback}",
        )
        arch_pos = _s(t3["data"].get("position"), 20).lower()
        arch_reason = _s(t3["data"].get("reason"), 1200)
        arch_constraints = _slist(t3["data"].get("architectural_constraints"))
        self.say(
            thread, arch_emp,
            CollaborationType.REVIEW if arch_pos == "endorse" else CollaborationType.CONCERN,
            f"[{arch_pos or 'review'}] {arch_reason}",
            to=cto_emp,
        )

        # 4. CEO makes the decision — approve direction or request changes.
        t4 = self._turn(
            "AI CEO", ("CEO",),
            "You are the AI CEO. Weigh the CTO answer and the Architect's position and "
            "DECIDE. Reply with ONLY JSON: {\"decision\":\"approved|changes_requested\","
            "\"rationale\":\"why\",\"agreed_constraints\":[\"...\"],"
            "\"open_concerns\":[\"...\"]}",
            f"{base}\nCTO agreed: {cto_agree}; pushback: {pushback}\n"
            f"Architect position: {arch_pos}; reason: {arch_reason}",
        )
        decision = _s(t4["data"].get("decision"), 30).lower() or "approved"
        rationale = _s(t4["data"].get("rationale"), 1500)
        agreed = _slist(t4["data"].get("agreed_constraints")) or proposed + arch_constraints
        concerns = _slist(t4["data"].get("open_concerns"))
        self.say(
            thread, ceo_emp,
            CollaborationType.APPROVAL if decision == "approved" else CollaborationType.DECISION,
            f"[{decision}] {rationale}",
            to=cto_emp,
        )

        # If the CEO requested changes, that is an escalation back to the CTO.
        if decision != "approved":
            self.say(
                thread, ceo_emp, CollaborationType.ESCALATION,
                f"Direction not approved as-is; CTO to revise. Concerns: {', '.join(concerns) or rationale}",
                to=cto_emp,
            )
        thread.status = "resolved"
        self.db.flush()

        return {
            "thread_id": str(thread.id),
            "decision": decision,
            "rationale": rationale,
            "agreed_constraints": agreed,
            "open_concerns": concerns,
            "cto_agreed": cto_agree,
            "architect_position": arch_pos,
            "turns": self._seq,
        }

    # -- review chain (AFTER planning) --------------------------------------

    def review_chain(self, project, plan_summary: str) -> dict:
        """Security then QA review the produced plan; either may reject/escalate."""
        thread = self.open_thread(project.id, f"Plan review — {project.name}", "plan_review")
        arch_emp = self._emp("CHIEF_ARCHITECT", "CTO")
        results = []

        for actor_label, codes, lens in (
            ("AI Security Engineer", ("SECURITY_ENGINEER",),
             "security, data protection and compliance"),
            ("AI QA Engineer", ("QA_ENGINEER",),
             "testability, acceptance-criteria quality and delivery risk"),
        ):
            t = self._turn(
                actor_label, codes,
                f"You are the {actor_label}. Review this delivery plan for {lens}. You "
                "have authority to REJECT. Do not rubber-stamp. Reply with ONLY JSON: "
                "{\"verdict\":\"approved|rejected\",\"findings\":[\"...\"],"
                "\"required_changes\":[\"...\"]}",
                f"Project: {project.name}\nPlan:\n{plan_summary}",
            )
            emp = t["employee"]
            verdict = _s(t["data"].get("verdict"), 20).lower() or "approved"
            findings = _slist(t["data"].get("findings"))
            changes = _slist(t["data"].get("required_changes"))
            self.say(
                thread, emp,
                CollaborationType.APPROVAL if verdict == "approved" else CollaborationType.REJECTION,
                f"[{verdict}] findings: {'; '.join(findings) or 'none'}"
                + (f" | required: {'; '.join(changes)}" if changes else ""),
                to=arch_emp,
            )
            if verdict != "approved":
                self.say(
                    thread, emp, CollaborationType.ESCALATION,
                    f"{t['role_title']} rejected the plan; escalating required changes to the Architect: "
                    + ("; ".join(changes) or "; ".join(findings)),
                    to=arch_emp,
                )
            results.append(
                {"reviewer": t["role_title"], "verdict": verdict, "findings": findings,
                 "required_changes": changes}
            )

        approved = all(r["verdict"] == "approved" for r in results)
        thread.status = "resolved"
        self.db.flush()
        return {"thread_id": str(thread.id), "approved": approved, "reviews": results, "turns": self._seq}

    # -- read model ---------------------------------------------------------

    def project_conversations(self, project_id: uuid.UUID) -> list[dict]:
        threads = self.db.scalars(
            select(ConversationThread)
            .where(ConversationThread.project_id == project_id)
            .order_by(ConversationThread.created_at)
        ).all()
        names = {e.id: e.name for e in self.db.scalars(select(AIEmployee)).all()}
        out = []
        for th in threads:
            msgs = self.db.scalars(
                select(ExecutionMessage)
                .where(ExecutionMessage.thread_id == th.id)
                .order_by(ExecutionMessage.sequence)
            ).all()
            out.append(
                {
                    "thread_id": str(th.id),
                    "title": th.title,
                    "kind": th.kind,
                    "status": th.status,
                    "messages": [
                        {
                            "sequence": m.sequence,
                            "type": m.message_type,
                            "from": names.get(m.speaker_employee_id),
                            "from_role": m.speaker_role,
                            "to": names.get(m.to_employee_id),
                            "content": m.content,
                        }
                        for m in msgs
                    ],
                }
            )
        return out

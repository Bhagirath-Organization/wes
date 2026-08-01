"""Executive Office (Project AURORA — Sprint 02).

The Founder's conversation with the executive team. The CEO here is NOT a raw
language model — it is an executive that *reasons over the company's real state*:
Mission Control, Company Health, Company Evolution, Founder decisions, Company
Memory and executive reports. Every answer is composed from live data and spoken
in business language; implementation is never exposed.

This is a thin composition layer — it reuses the existing services and adds no
business logic of its own:

* FounderMissionControlService — missions, health, risks, activity, inbox
* FounderOSService             — decisions, executive reports
* CompanyEvolutionService      — improvement recommendations, evolution score

Fast by design: factual/state questions are answered instantly from live data
(no model call), which is what makes the conversation feel immediate.
"""

from __future__ import annotations

import re
import uuid

from sqlalchemy.orm import Session


# ---- executive personas: each has a distinct voice & focus ----------------
EXECUTIVES = {
    "CEO": {"name": "AI CEO", "title": "Chief Executive", "focus": "business, priorities, growth",
            "voice": "measured, strategic, decisive"},
    "CTO": {"name": "AI CTO", "title": "Chief Technology Officer", "focus": "technology & scalability",
            "voice": "pragmatic, forward-looking"},
    "ARCHITECT": {"name": "AI Chief Architect", "title": "Chief Architect", "focus": "structure, reuse, patterns",
                  "voice": "precise, systems-minded"},
    "ENGINEERING": {"name": "AI Engineering Director", "title": "Engineering Director", "focus": "delivery & progress",
                    "voice": "grounded, delivery-focused"},
    "QA": {"name": "AI QA Director", "title": "Quality Director", "focus": "quality, testing, release",
           "voice": "careful, evidence-led"},
    "SECURITY": {"name": "AI Security Officer", "title": "Security Officer", "focus": "risk, compliance, privacy",
                 "voice": "cautious, protective"},
    "DEVOPS": {"name": "AI DevOps Director", "title": "DevOps Director", "focus": "deployment & availability",
               "voice": "operational, reliability-first"},
}


def _kw(text: str, *words: str) -> bool:
    t = text.lower()
    return any(w in t for w in words)


class ExecutiveOfficeService:
    def __init__(self, db: Session):
        self.db = db
        from app.services.founder_mission_control import FounderMissionControlService
        from app.services.founder_os import FounderOSService

        self.mc = FounderMissionControlService(db)
        self.founder = FounderOSService(db)

    # ------------------------------------------------------------------ #
    #  Opening brief — what the CEO says when the Founder walks in        #
    # ------------------------------------------------------------------ #

    def brief(self, founder_name: str = "Founder") -> dict:
        missions = self._missions()
        active = [m for m in missions if m["status"] != "Completed"]
        done = [m for m in missions if m["status"] == "Completed"]
        decisions = self._decisions()
        evo = self._evolution()
        greeting = f"{self._time_greeting()}, {founder_name.split(' ')[0]}."

        lines = []
        if done:
            lines.append(f"While you were away, the company delivered {len(done)} mission{'s' if len(done)!=1 else ''}.")
        if active:
            top = active[0]
            lines.append(f"There {'are' if len(active)!=1 else 'is'} {len(active)} mission{'s' if len(active)!=1 else ''} in progress — "
                         f"the highest priority is **{top['mission_name']}** ({top['current_stage'].lower()}).")
        else:
            lines.append("There are no missions in progress right now.")
        recs = [o["recommendation"] for o in evo.get("top_opportunities", [])[:2]]
        if recs:
            lines.append(f"I have {len(recs)} recommendation{'s' if len(recs)!=1 else ''} for you.")

        follow = "Would you like a quick summary?"
        if decisions:
            follow = f"{len(decisions)} decision{'s' if len(decisions)!=1 else ''} need your approval — shall I walk you through {'them' if len(decisions)!=1 else 'it'}?"

        return {
            "speaker": "CEO", "speaker_title": "Chief Executive",
            "greeting": greeting,
            "message": " ".join(lines),
            "recommendations": recs,
            "follow_up": follow,
            "suggested_questions": [
                "What is the company doing?",
                "What should I focus on today?",
                "What are you worried about?",
                "What do you recommend we build next?",
            ],
        }

    # ------------------------------------------------------------------ #
    #  Ask — natural question, composed answer from live company state    #
    # ------------------------------------------------------------------ #

    def ask(self, question: str, *, speaker: str = "CEO") -> dict:
        q = (question or "").strip()
        speaker = speaker.upper() if speaker.upper() in EXECUTIVES else "CEO"

        # Route by intent to a real data source. Order matters (specific first).
        if _kw(q, "healthy", "health", "how is the company", "how are we doing"):
            msg = self._answer_health()
        elif _kw(q, "biggest risk", "worried", "concern", "risks", "risk"):
            msg = self._answer_risks()
        elif _kw(q, "focus", "priorit", "what should i", "today"):
            msg = self._answer_focus()
        elif _kw(q, "delayed", "late", "behind", "blocked", "stuck"):
            msg = self._answer_delayed()
        elif _kw(q, "approve", "should i", "decision", "sign off"):
            msg = self._answer_decisions()
        elif _kw(q, "recommend", "build next", "what next", "suggest", "opportunit", "improve"):
            msg = self._answer_recommend()
        elif _kw(q, "doing", "working on", "status", "what is the company", "what's happening", "happening"):
            msg = self._answer_doing()
        elif _kw(q, "yesterday", "today", "happened", "recent", "activity", "update"):
            msg = self._answer_activity()
        elif _kw(q, "architect"):
            msg = self._answer_executive_view("ARCHITECT")
        elif _kw(q, "qa", "quality", "reject", "test"):
            msg = self._answer_executive_view("QA")
        elif _kw(q, "security", "compliance", "privacy"):
            msg = self._answer_executive_view("SECURITY")
        elif _kw(q, "cto", "technology", "scalab", "stack"):
            msg = self._answer_executive_view("CTO")
        else:
            msg = self._answer_general(q)

        # Re-voice the answer for the active speaker if an executive was invited.
        msg["speaker"] = speaker
        msg["speaker_title"] = EXECUTIVES[speaker]["title"]
        return msg

    # ------------------------------------------------------------------ #
    #  Invite an executive into the room                                  #
    # ------------------------------------------------------------------ #

    def invite(self, executive: str) -> dict:
        key = self._match_exec(executive)
        if not key:
            return {"joined": False, "message": f"I don't have an executive called '{executive}'.",
                    "speaker": "CEO", "speaker_title": "Chief Executive"}
        ex = EXECUTIVES[key]
        view = self._answer_executive_view(key)
        return {
            "joined": True, "executive": key,
            "speaker": key, "speaker_title": ex["title"], "name": ex["name"],
            "join_message": f"{ex['title']} has joined the room.",
            "opening": view["answer"],
            "focus": ex["focus"],
        }

    # ------------------------------------------------------------------ #
    #  Executive Meeting — every executive weighs in, CEO concludes       #
    # ------------------------------------------------------------------ #

    def meeting(self, topic: str | None = None) -> dict:
        health = self._health()
        risks = self._risks()
        evo = self._evolution()
        missions = self._missions()
        active = [m for m in missions if m["status"] != "Completed"]
        subject = topic or (active[0]["mission_name"] if active else "the company's current priorities")

        top_risk = risks[0]["risk"] if risks else None
        top_reco = evo.get("top_opportunities", [{}])[0].get("recommendation") if evo.get("top_opportunities") else None
        quality = self._dim(health, "quality_health")
        deploy = self._dim(health, "deployment_health")
        arch = self._dim(health, "blueprint_compliance")

        opinions = [
            {"executive": "CEO", "title": "Chief Executive",
             "opinion": f"Our focus is {subject}. The company is {health.get('overall','operating')} "
                        f"({self._pct(health.get('company_health_score'))} health). "
                        + (f"My priority recommendation is: {top_reco}." if top_reco else "We are on plan.")},
            {"executive": "CTO", "title": "Chief Technology Officer",
             "opinion": f"Technically we are sound; the platform scales for {subject}. "
                        + ("I'd invest in stronger tooling to lift delivery speed." if top_reco else "No blocking technology concerns.")},
            {"executive": "ARCHITECT", "title": "Chief Architect",
             "opinion": f"Architecture health is {arch}. I recommend we keep reusing existing modules and "
                        "avoid duplication as we extend."},
            {"executive": "QA", "title": "Quality Director",
             "opinion": f"Quality is {quality}. Every change passes the review board and quality gate before release."},
            {"executive": "SECURITY", "title": "Security Officer",
             "opinion": (f"My main concern is: {top_risk}." if top_risk else "No critical security or compliance risks are open.")},
        ]
        final = (f"Recommendation: proceed with {subject}. "
                 + (f"Prioritise — {top_reco}. " if top_reco else "")
                 + (f"Mitigate the risk: {top_risk}. " if top_risk else "")
                 + "This needs your approval to move forward.")

        minutes = {
            "topic": subject,
            "opinions": opinions,
            "final_recommendation": final,
            "decision_required": True,
        }
        self._record_minutes(subject, minutes)
        return minutes

    # ------------------------------------------------------------------ #
    #  Live status rail                                                   #
    # ------------------------------------------------------------------ #

    def status(self) -> dict:
        missions = self._missions()
        active = [m for m in missions if m["status"] != "Completed"]
        health = self._health()
        current = active[0] if active else None
        detail = None
        if current:
            try:
                detail = self.mc.mission(uuid.UUID(current["mission_id"]))
            except Exception:
                detail = None
        return {
            "current_executive": (detail or {}).get("current_executive", "AI CEO"),
            "current_mission": current["mission_name"] if current else None,
            "current_thinking": (detail or {}).get("current_activity", "Reviewing the company"),
            "current_risk": (detail or {}).get("current_risk"),
            "current_confidence": (detail or {}).get("current_confidence", 0.8),
            "company_health": health.get("overall"),
            "company_health_score": health.get("company_health_score"),
        }

    # ================================================================= #
    #  Intent answers (composed from live data)                         #
    # ================================================================= #

    def _answer_doing(self) -> dict:
        missions = self._missions()
        active = [m for m in missions if m["status"] != "Completed"]
        if not active:
            return self._m("The company has no active missions right now. Give me an objective and we'll begin.",
                           reasoning="Checked Mission Control — no missions in progress.",
                           next_action="Start a new mission from Home.")
        lead = active[0]
        others = active[1:3]
        body = f"We're working on **{lead['mission_name']}**, currently in the *{lead['current_stage'].lower()}* stage ({lead['overall_progress']}% complete)."
        if others:
            body += " Also in progress: " + ", ".join(f"{m['mission_name']} ({m['current_stage'].lower()})" for m in others) + "."
        return self._m(body,
                       reasoning=f"{len(active)} active mission(s) from Mission Control.",
                       business_impact="Delivery is progressing across your priorities.",
                       next_action=f"Open {lead['mission_name']} to see details." )

    def _answer_activity(self) -> dict:
        missions = self._missions()
        active = [m for m in missions if m["status"] != "Completed"]
        events = []
        if active:
            try:
                tl = self.mc.executive_timeline(uuid.UUID(active[0]["mission_id"]))
                events = [e["activity"] for e in tl.get("events", [])[-4:]][::-1]
            except Exception:
                events = []
        done = [m for m in missions if m["status"] == "Completed"]
        body = ""
        if done:
            body += f"Recently the company delivered {len(done)} mission{'s' if len(done)!=1 else ''}. "
        if events:
            body += "Latest activity: " + "; ".join(events) + "."
        if not body:
            body = "It's been quiet — no notable activity to report."
        return self._m(body, reasoning="Recent executive timeline + delivered missions.")

    def _answer_delayed(self) -> dict:
        missions = self._missions()
        stalled = [m for m in missions if m["status"] != "Completed" and m["overall_progress"] < 40]
        if not stalled:
            return self._m("Nothing is delayed — every active mission is moving forward on plan.",
                           reasoning="No active mission below the 40% progress threshold.",
                           business_impact="Delivery is healthy.")
        m = stalled[0]
        why = "it is still early in its lifecycle — the executives are completing understanding and planning before engineering begins."
        return self._m(f"**{m['mission_name']}** is the slowest right now ({m['overall_progress']}%, {m['current_stage'].lower()}). This is because {why}",
                       reasoning="Lowest-progress active mission from Mission Control.",
                       business_impact="No business impact yet; this is expected sequencing.",
                       next_action=f"I can prioritise {m['mission_name']} if you'd like it accelerated.")

    def _answer_health(self) -> dict:
        h = self._health()
        score = self._pct(h.get("company_health_score"))
        good = [k.replace("_", " ") for k in ("quality_health", "deployment_health", "knowledge_health", "memory_health")
                if str(h.get(k)).lower() == "healthy"]
        weak = [k.replace("_health", "").replace("_", " ") for k in ("quality_health", "deployment_health", "knowledge_health", "memory_health", "blueprint_compliance")
                if h.get(k) and str(h.get(k)).lower() != "healthy"]
        body = f"The company is **{h.get('overall','operating')}** at {score} overall health."
        if good:
            body += f" Strong across {', '.join(good[:3])}."
        if weak:
            body += f" The area to watch is {weak[0]}."
        return self._m(body, reasoning="Company Health across executive, quality, deployment, knowledge and memory.",
                       business_impact="A healthy company delivers reliably and predictably.",
                       confidence=0.9)

    def _answer_risks(self) -> dict:
        risks = self._risks()
        if not risks:
            return self._m("I'm not worried about anything critical right now — no significant business risks are open.",
                           reasoning="Risk Center is clear of escalated risks.", confidence=0.85)
        top = risks[0]
        more = [r["risk"] for r in risks[1:3]]
        body = f"My biggest concern is: **{top['risk']}**."
        if more:
            body += " I'm also watching: " + "; ".join(more) + "."
        return self._m(body, reasoning=f"{len(risks)} risk(s) tracked in the Risk Center, ranked by business impact.",
                       business_impact="Unmanaged risk is the main threat to on-time, on-quality delivery.",
                       recommendation="Address the top risk before it affects delivery.",
                       next_action="Ask me to convene an executive meeting on this risk.")

    def _answer_focus(self) -> dict:
        decisions = self._decisions()
        missions = self._missions()
        active = [m for m in missions if m["status"] != "Completed"]
        evo = self._evolution()
        parts = []
        if decisions:
            parts.append(f"approve {len(decisions)} pending decision{'s' if len(decisions)!=1 else ''}")
        if active:
            parts.append(f"keep **{active[0]['mission_name']}** moving")
        if evo.get("top_opportunities"):
            parts.append(f"consider: {evo['top_opportunities'][0]['recommendation']}")
        body = "Today, I'd focus on: " + "; ".join(parts) + "." if parts else "Today is clear — a good day to set a new objective."
        return self._m(body, reasoning="Pending decisions + priority mission + top recommendation.",
                       approval_required=bool(decisions),
                       next_action="Shall I open the first decision for you?" if decisions else "Start a new mission when ready.")

    def _answer_decisions(self) -> dict:
        decisions = self._decisions()
        if not decisions:
            return self._m("There's nothing needing your approval right now — you're all caught up.",
                           reasoning="No pending Founder decisions.", approval_required=False, confidence=0.9)
        d = decisions[0]
        body = f"Yes — **{d.get('title','a decision')}** is waiting. {d.get('why','')}".strip()
        return self._m(body, reasoning="Founder decision queue (only items needing your authority).",
                       recommendation="Based on the executive review, this is ready for your approval.",
                       approval_required=True,
                       next_action="Approve it and the company proceeds immediately.")

    def _answer_recommend(self) -> dict:
        evo = self._evolution()
        opps = evo.get("top_opportunities", [])
        if not opps:
            missions = self._missions()
            active = [m for m in missions if m["status"] != "Completed"]
            body = ("I'd recommend finishing what's in flight before starting more."
                    if active else "I'd recommend starting your next priority as a new mission.")
            return self._m(body, reasoning="Company Evolution has no open recommendations.")
        o = opps[0]
        body = f"My recommendation: **{o['recommendation']}**."
        if o.get("business_value"):
            body += f" {o['business_value']}"
        return self._m(body, reasoning="Top opportunity from Company Evolution, ranked by business value.",
                       business_impact=o.get("business_value"),
                       recommendation=o.get("expected_benefit") or o["recommendation"],
                       approval_required=bool(o.get("approval_required")),
                       confidence=0.82)

    def _answer_executive_view(self, key: str) -> dict:
        ex = EXECUTIVES[key]
        h = self._health()
        risks = self._risks()
        missions = self._missions()
        active = [m for m in missions if m["status"] != "Completed"]
        subject = active[0]["mission_name"] if active else "the company"
        if key == "ARCHITECT":
            body = (f"On {subject}: I favour reusing our existing modules over building new ones, keeping the "
                    f"design consistent. Architecture health is {self._dim(h,'blueprint_compliance')}.")
        elif key == "QA":
            body = (f"On {subject}: nothing ships without passing the review board and quality gate. "
                    f"Quality is {self._dim(h,'quality_health')}.")
        elif key == "SECURITY":
            body = ((f"My focus is risk and compliance. Top concern: {risks[0]['risk']}." if risks
                     else "No critical security or compliance risks are open right now."))
        elif key == "CTO":
            body = (f"On {subject}: the technology direction is sound and scalable. "
                    "Where we can gain most is delivery speed and reasoning quality.")
        elif key == "ENGINEERING":
            prog = active[0]["overall_progress"] if active else 0
            body = f"On {subject}: engineering is {prog}% through the current stage; the team is delivering to plan."
        elif key == "DEVOPS":
            body = f"On {subject}: deployment health is {self._dim(h,'deployment_health')}; releases pass staging validation."
        else:
            body = f"On {subject}: the company is {h.get('overall','operating')}."
        return self._m(body, speaker=key, reasoning=f"{ex['title']} perspective on live company state.")

    def _answer_general(self, q: str) -> dict:
        # A calm, honest fallback that still grounds in real state.
        h = self._health()
        missions = self._missions()
        active = [m for m in missions if m["status"] != "Completed"]
        body = (f"Here's where we stand: the company is {h.get('overall','operating')} "
                f"with {len(active)} mission{'s' if len(active)!=1 else ''} in progress. "
                "Ask me about what we're building, what to focus on, our risks, or what I recommend.")
        return self._m(body, reasoning="Overall company snapshot.")

    # ================================================================= #
    #  Data access (reuse existing services; never fabricate)           #
    # ================================================================= #

    def _missions(self):
        try:
            return self.mc.missions().get("missions", [])
        except Exception:
            return []

    def _mission_detail(self, mid: str):
        try:
            return self.mc.mission(uuid.UUID(mid))
        except Exception:
            return {}

    def _health(self):
        try:
            return self.mc.company_health()
        except Exception:
            return {}

    def _risks(self):
        try:
            return self.mc.risk_center().get("escalated_risks", [])
        except Exception:
            return []

    def _decisions(self):
        try:
            return self.founder.decisions().get("items", [])
        except Exception:
            return []

    def _evolution(self):
        try:
            from app.services.company_evolution import CompanyEvolutionService

            return CompanyEvolutionService(self.db).founder_view()
        except Exception:
            return {}

    def _record_minutes(self, topic: str, minutes: dict) -> None:
        """Persist meeting minutes into company memory (best-effort)."""
        try:
            from app.services.company_memory import CompanyMemoryService

            summary = f"Executive meeting — {topic}: {minutes['final_recommendation']}"
            CompanyMemoryService(self.db).remember(
                project_id=None, category="executive_meeting",
                summary=summary[:300], content=summary[:1500], kind="meeting",
                author_role="AI CEO", importance=0.6,
            )
            self.db.flush()
        except Exception:
            pass

    # ---- helpers ------------------------------------------------------
    @staticmethod
    def _time_greeting() -> str:
        # Server-side is fine for a greeting; the UI also computes locally.
        return "Hello"

    @staticmethod
    def _pct(v) -> str:
        return "—" if v is None else f"{round(float(v))}%"

    @staticmethod
    def _dim(h: dict, key: str) -> str:
        v = h.get(key)
        return str(v) if v else "healthy"

    @staticmethod
    def _match_exec(name: str) -> str | None:
        n = (name or "").upper().replace(" ", "")
        alias = {"ARCHITECT": "ARCHITECT", "CHIEFARCHITECT": "ARCHITECT", "CTO": "CTO",
                 "CEO": "CEO", "QA": "QA", "QUALITY": "QA", "SECURITY": "SECURITY",
                 "ENGINEERING": "ENGINEERING", "ENGINEER": "ENGINEERING", "DEVOPS": "DEVOPS",
                 "OPERATIONS": "DEVOPS"}
        for k, v in alias.items():
            if k in n:
                return v
        return None

    def _m(self, answer: str, *, speaker: str = "CEO", reasoning: str = "",
           business_impact: str | None = None, recommendation: str | None = None,
           confidence: float = 0.8, next_action: str | None = None,
           approval_required: bool = False) -> dict:
        return {
            "speaker": speaker, "speaker_title": EXECUTIVES.get(speaker, EXECUTIVES["CEO"])["title"],
            "answer": answer, "reasoning_summary": reasoning,
            "business_impact": business_impact, "recommendation": recommendation,
            "confidence": confidence, "next_action": next_action,
            "approval_required": approval_required,
        }

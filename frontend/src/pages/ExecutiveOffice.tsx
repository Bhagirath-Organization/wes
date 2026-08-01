import { useEffect, useRef, useState } from "react";

import { useSession } from "../auth/SessionContext";
import {
  founderApi, type ExecMeeting, type ExecMessage, type ExecStatus,
} from "../api/founder";
import { Badge, Thinking } from "../components/ui/kit";

/* ---------------------------------------------------------------------- */
/*  Executive Office — the Founder's conversation with the CEO & team.     */
/*  Every answer comes from live company state; implementation is hidden.  */
/* ---------------------------------------------------------------------- */

type Msg =
  | { kind: "exec"; m: ExecMessage }
  | { kind: "me"; text: string }
  | { kind: "join"; text: string }
  | { kind: "meeting"; minutes: ExecMeeting };

const EXEC_INITIALS: Record<string, string> = {
  CEO: "CE", CTO: "CT", ARCHITECT: "CA", ENGINEERING: "ED", QA: "QA", SECURITY: "SO", DEVOPS: "DO",
};
const ROSTER = [
  { key: "CTO", label: "CTO" }, { key: "Chief Architect", label: "Architect" },
  { key: "QA", label: "QA" }, { key: "Security", label: "Security" },
];

function greeting() {
  const h = new Date().getHours();
  return h < 12 ? "Good morning" : h < 18 ? "Good afternoon" : "Good evening";
}

/* render **bold** inside an executive answer */
function RichText({ text }: { text: string }) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return <>{parts.map((p, i) => p.startsWith("**") && p.endsWith("**")
    ? <strong key={i}>{p.slice(2, -2)}</strong> : <span key={i}>{p}</span>)}</>;
}

export function ExecutiveOffice() {
  const { user } = useSession();
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [chips, setChips] = useState<string[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [speaker, setSpeaker] = useState("CEO");
  const [status, setStatus] = useState<ExecStatus | null>(null);
  const threadRef = useRef<HTMLDivElement>(null);

  // Opening brief + live status.
  useEffect(() => {
    let alive = true;
    founderApi.brief().then((b) => {
      if (!alive) return;
      const first = user?.full_name?.split(" ")[0] ?? "Founder";
      setMsgs([{ kind: "exec", m: {
        speaker: "CEO", speaker_title: "Chief Executive",
        answer: `${greeting()}, ${first}. ${b.message} ${b.follow_up}`,
        recommendation: b.recommendations[0] ?? null,
      } }]);
      setChips(b.suggested_questions);
    }).catch(() => {
      setMsgs([{ kind: "exec", m: { speaker: "CEO", speaker_title: "Chief Executive",
        answer: "Good to see you. Ask me anything about the company." } }]);
    });
    founderApi.execStatus().then((s) => alive && setStatus(s)).catch(() => {});
    return () => { alive = false; };
  }, [user]);

  useEffect(() => {
    threadRef.current?.scrollTo({ top: threadRef.current.scrollHeight, behavior: "smooth" });
  }, [msgs, busy]);

  async function send(text: string) {
    const q = text.trim();
    if (!q || busy) return;
    setInput(""); setChips([]);
    setMsgs((m) => [...m, { kind: "me", text: q }]);
    setBusy(true);

    // Natural-language intents handled client-side: invite & meeting.
    const lower = q.toLowerCase();
    try {
      if (/\b(invite|bring in|call in|ask the)\b/.test(lower) && /(cto|architect|qa|quality|security|engineer|devops|ops)/.test(lower)) {
        const res = await founderApi.invite(q);
        if (res.joined && res.executive) {
          setSpeaker(res.executive);
          setMsgs((m) => [...m, { kind: "join", text: res.join_message ?? "" },
            { kind: "exec", m: { speaker: res.speaker, speaker_title: res.speaker_title, answer: res.opening ?? "" } }]);
        } else {
          setMsgs((m) => [...m, { kind: "exec", m: { speaker: "CEO", speaker_title: "Chief Executive", answer: res.message ?? "" } }]);
        }
      } else if (/\b(executive meeting|call a meeting|convene|board meeting|meeting)\b/.test(lower)) {
        const minutes = await founderApi.meeting(undefined);
        setMsgs((m) => [...m, { kind: "meeting", minutes }]);
      } else {
        const m = await founderApi.ask(q, speaker);
        setMsgs((prev) => [...prev, { kind: "exec", m }]);
      }
    } catch {
      setMsgs((m) => [...m, { kind: "exec", m: { speaker: "CEO", speaker_title: "Chief Executive",
        answer: "I couldn't reach that part of the company just now. Please try again." } }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="wes-office">
      {/* ------- conversation ------- */}
      <div className="wes-conv">
        <div className="wes-conv-head">
          <div className="wes-msg-av" style={{ width: 40, height: 40, borderRadius: 13 }}>CE</div>
          <div>
            <div className="wes-conv-title">Executive Office</div>
            <div className="wes-conv-sub">
              {speaker === "CEO" ? "In session with your Chief Executive" : `In session — ${speaker} present`}
            </div>
          </div>
        </div>

        <div className="wes-thread" ref={threadRef}>
          {msgs.map((m, i) => <MessageView key={i} msg={m} />)}
          {busy && <ThinkingBubble speaker={speaker} />}
        </div>

        <div className="wes-composer">
          {chips.length > 0 && (
            <div className="wes-chips">
              {chips.map((c) => <button key={c} className="wes-chip" onClick={() => send(c)}>{c}</button>)}
              <button className="wes-chip" onClick={() => send("Call an executive meeting")}>Call an executive meeting</button>
            </div>
          )}
          <div className="wes-composer-box">
            <textarea
              rows={1} value={input} placeholder="Ask your CEO anything…"
              onChange={(e) => { setInput(e.target.value); e.target.style.height = "auto"; e.target.style.height = `${Math.min(e.target.scrollHeight, 160)}px`; }}
              onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(input); } }}
            />
            <button className="wes-send" onClick={() => send(input)} disabled={busy || !input.trim()} aria-label="Send">↑</button>
          </div>
        </div>
      </div>

      {/* ------- live status rail ------- */}
      <aside className="wes-rail">
        <div className="wes-rail-card">
          <div className="wes-rail-k">In the room</div>
          <div className="wes-rail-execs" style={{ marginTop: 12 }}>
            <div className="wes-rail-exec">
              <div className="wes-msg-av">CE</div>
              <div><div className="wes-rail-v" style={{ fontSize: "var(--wes-fs-sm)" }}>Chief Executive</div>
                <div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>Leading the session</div></div>
            </div>
            {ROSTER.map((r) => (
              <button key={r.key} className="wes-rail-exec" style={{ background: "none", border: 0, cursor: "pointer", textAlign: "left", padding: 0 }}
                onClick={() => send(`Invite the ${r.key}`)}>
                <div className="wes-msg-av" style={{ background: "var(--wes-bg-4)", color: "var(--wes-text-3)" }}>{EXEC_INITIALS[r.key.toUpperCase()] ?? r.label.slice(0, 2)}</div>
                <div><div className="wes-rail-v" style={{ fontSize: "var(--wes-fs-sm)" }}>{r.label}</div>
                  <div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>Invite to join</div></div>
              </button>
            ))}
          </div>
        </div>

        {status && (
          <div className="wes-rail-card">
            <div className="wes-rail-k">Live status</div>
            <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 14 }}>
              <RailRow k="Current focus" v={status.current_mission ?? "No active mission"} />
              <RailRow k="Executive" v={status.current_executive} />
              <div>
                <div className="wes-rail-k">Thinking</div>
                <div className="wes-row" style={{ marginTop: 4 }}>
                  <span className="wes-rail-v" style={{ fontSize: "var(--wes-fs-sm)" }}>{status.current_thinking}</span><Thinking />
                </div>
              </div>
              <div className="wes-between">
                <div><div className="wes-rail-k">Confidence</div><div className="wes-rail-v">{Math.round((status.current_confidence ?? 0) * 100)}%</div></div>
                <div style={{ textAlign: "right" }}><div className="wes-rail-k">Health</div>
                  <Badge tone={status.company_health === "healthy" ? "ok" : "warn"} dot>{status.company_health ?? "—"}</Badge></div>
              </div>
              {status.current_risk && <RailRow k="Watching" v={status.current_risk} />}
            </div>
          </div>
        )}
      </aside>
    </div>
  );
}

/* -------------------- message renderers -------------------- */

function MessageView({ msg }: { msg: Msg }) {
  if (msg.kind === "join") return <div className="wes-join">✦ <b>{msg.text}</b></div>;
  if (msg.kind === "me") return (
    <div className="wes-msg me">
      <div className="wes-msg-av">You</div>
      <div className="wes-msg-body"><div className="wes-bubble">{msg.text}</div></div>
    </div>
  );
  if (msg.kind === "meeting") return <MeetingView minutes={msg.minutes} />;

  const m = msg.m;
  const key = (m.speaker || "CEO").toUpperCase();
  return (
    <div className="wes-msg">
      <div className="wes-msg-av">{EXEC_INITIALS[key] ?? key.slice(0, 2)}</div>
      <div className="wes-msg-body">
        <div className="wes-msg-who">
          <span className="wes-msg-name">{m.speaker_title || "Chief Executive"}</span>
          {m.approval_required && <Badge tone="warn">Approval needed</Badge>}
        </div>
        <div className="wes-bubble">
          <RichText text={m.answer} />
          {(m.business_impact || m.recommendation || m.next_action) && (
            <div className="wes-detail">
              {m.recommendation && <div className="wes-detail-row"><b>Recommend</b><span>{m.recommendation}</span></div>}
              {m.business_impact && <div className="wes-detail-row"><b>Impact</b><span>{m.business_impact}</span></div>}
              {m.next_action && <div className="wes-detail-row"><b>Next</b><span>{m.next_action}</span></div>}
            </div>
          )}
          {m.reasoning_summary && <div className="wes-reason">{m.reasoning_summary}
            {typeof m.confidence === "number" && ` · ${Math.round(m.confidence * 100)}% confident`}</div>}
        </div>
      </div>
    </div>
  );
}

function MeetingView({ minutes }: { minutes: ExecMeeting }) {
  return (
    <div className="wes-msg" style={{ maxWidth: 820 }}>
      <div className="wes-msg-av">✦</div>
      <div className="wes-msg-body" style={{ width: "100%" }}>
        <div className="wes-msg-who"><span className="wes-msg-name">Executive Meeting</span><Badge tone="info">{minutes.topic.slice(0, 40)}</Badge></div>
        <div className="wes-bubble">
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {minutes.opinions.map((o, i) => (
              <div key={i}>
                <div className="wes-msg-name" style={{ fontSize: "var(--wes-fs-sm)", color: "var(--wes-brand-ink)" }}>{o.title}</div>
                <div style={{ fontSize: "var(--wes-fs-sm)", color: "var(--wes-text-2)", marginTop: 2 }}>{o.opinion}</div>
              </div>
            ))}
          </div>
          <div className="wes-detail" style={{ marginTop: 14, borderTop: "1px solid var(--wes-line)", paddingTop: 12 }}>
            <div className="wes-detail-row"><b>CEO decision</b><span><RichText text={minutes.final_recommendation} /></span></div>
          </div>
          {minutes.decision_required && <div style={{ marginTop: 10 }}><Badge tone="warn">Your approval required</Badge></div>}
        </div>
      </div>
    </div>
  );
}

function ThinkingBubble({ speaker }: { speaker: string }) {
  const key = speaker.toUpperCase();
  return (
    <div className="wes-msg">
      <div className="wes-msg-av">{EXEC_INITIALS[key] ?? "CE"}</div>
      <div className="wes-msg-body">
        <div className="wes-bubble" style={{ display: "inline-flex", padding: "14px 18px" }}><Thinking /></div>
      </div>
    </div>
  );
}

function RailRow({ k, v }: { k: string; v: string }) {
  return <div><div className="wes-rail-k">{k}</div><div className="wes-rail-v" style={{ fontSize: "var(--wes-fs-sm)", lineHeight: 1.4 }}>{v}</div></div>;
}

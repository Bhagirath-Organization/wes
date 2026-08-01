import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  founderApi, type OpActivity, type OpAutomation, type OpAutonomy, type OpDecisions,
  type OpEscalations, type OpPolicies, type OpPolicy, type OpQueue, type OpTrust,
} from "../api/founder";
import { Badge, Card, Empty, ProgressRing, Skeleton, Thinking } from "../components/ui/kit";

type Tab = "live" | "decisions" | "policy" | "escalations" | "automation" | "trust";
const FOUNDER_CONTROLS = ["Approve", "Pause", "Resume", "Delegate", "Override", "Request review"];

export function CompanyOperations() {
  const navigate = useNavigate();
  const [queue, setQueue] = useState<OpQueue | null>(null);
  const [activity, setActivity] = useState<OpActivity | null>(null);
  const [decisions, setDecisions] = useState<OpDecisions | null>(null);
  const [tab, setTab] = useState<Tab>("live");

  useEffect(() => {
    const load = () => {
      founderApi.opQueue().then(setQueue).catch(() => {});
      founderApi.opActivity().then(setActivity).catch(() => {});
      founderApi.opDecisions().then(setDecisions).catch(() => {});
    };
    load();
    const iv = setInterval(load, 15000); // live operating state
    return () => clearInterval(iv);
  }, []);

  return (
    <div className="wes-page wes-stack">
      <section className="wes-brain-hero wes-in wes-in-1">
        <div className="wes-eyebrow" style={{ marginBottom: 8 }}>Company Operations</div>
        <h1 className="wes-h1">Your company runs itself.</h1>
        <p className="wes-dim" style={{ marginTop: 6 }}>It analyses, prioritises, delegates, reviews and learns continuously — you approve only what's strategic.</p>
        {decisions && (
          <div className="wes-row" style={{ marginTop: 20, gap: 14, flexWrap: "wrap" }}>
            <span className="wes-row" style={{ gap: 8 }}><span className="wes-live-dot" /><span className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)" }}>{decisions.company_level} decisions made autonomously · {decisions.founder_level} awaiting you</span></span>
          </div>
        )}
      </section>

      {queue && (
        <section className="wes-ops-summary wes-in wes-in-2">
          <Stat n={queue.summary.running} k="Running" />
          <Stat n={queue.summary.completed} k="Completed" />
          <Stat n={queue.summary.waiting_founder} k="Awaiting you" tone="warn" />
          <Stat n={queue.summary.blocked} k="Needs attention" tone={queue.summary.blocked ? "warn" : undefined} />
        </section>
      )}

      <div className="wes-seg-nav wes-in wes-in-3" style={{ flexWrap: "wrap" }}>
        {([["live", "Live Operations"], ["decisions", "Autonomous Decisions"], ["policy", "Approval Policy"], ["escalations", "Escalations"], ["automation", "Automation"], ["trust", "Trust"]] as const).map(([v, l]) => (
          <button key={v} className={`wes-seg-btn${tab === v ? " active" : ""}`} onClick={() => setTab(v)}>{l}</button>
        ))}
      </div>

      {tab === "live" && (
        <div className="wes-grid cols-2 wes-in">
          {/* operation queue */}
          <section>
            <div className="wes-h3" style={{ marginBottom: 14 }}>Operation Queue</div>
            {!queue ? <Card><Skeleton h={160} /></Card> : (
              <div className="wes-stack" style={{ gap: 14 }}>
                <OpColumn title="Running" dot="running" items={queue.running} empty="Nothing running — the company is up to date." />
                <OpColumn title="Waiting for you" dot="waiting" items={queue.waiting_for_founder} onClick={() => setTab("decisions")} />
                {queue.blocked.length > 0 && <OpColumn title="Needs attention" dot="blocked" items={queue.blocked} />}
                <OpColumn title="Completed recently" dot="done" items={queue.completed_recently} />
              </div>
            )}
          </section>
          {/* activity stream */}
          <section>
            <div className="wes-between" style={{ marginBottom: 14 }}><div className="wes-h3">Activity Stream</div><span className="wes-row" style={{ gap: 6 }}><span className="wes-live-dot" /><span className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>live</span></span></div>
            <Card>
              {!activity ? <Skeleton h={200} /> : (
                <div className="wes-actstream">
                  {activity.events.map((e, i) => (
                    <div key={i} className="wes-act">
                      <span className={`wes-act-dot ${e.severity}`} />
                      <div><div style={{ fontSize: "var(--wes-fs-sm)" }}>{e.headline}{e.count > 1 ? ` (×${e.count})` : ""}</div>
                        {e.detail && <div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)", marginTop: 2 }}>{e.detail}</div>}</div>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </section>
        </div>
      )}

      {tab === "decisions" && <DecisionsView decisions={decisions} onOpen={() => navigate("/command")} />}
      {tab === "policy" && <PolicyView />}
      {tab === "escalations" && <EscalationsView onOpen={() => navigate("/command")} />}
      {tab === "automation" && <AutomationView />}
      {tab === "trust" && <TrustView />}

      {/* executive autonomy */}
      {tab === "live" && <ExecutiveAutonomy />}
    </div>
  );
}

/* ---------------- operation column ---------------- */
function OpColumn({ title, dot, items, empty, onClick }: { title: string; dot: string; items: { operation: string; owner: string; status: string; progress: number; note: string | null }[]; empty?: string; onClick?: () => void }) {
  return (
    <div>
      <div className="wes-op-col-head"><span className={`wes-op-col-dot ${dot}`} /><span style={{ fontWeight: 600, fontSize: "var(--wes-fs-sm)" }}>{title}</span><span className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>{items.length}</span></div>
      {items.length ? items.slice(0, 5).map((o, i) => (
        <div key={i} className="wes-op-item" style={onClick ? { cursor: "pointer" } : undefined} onClick={onClick} role={onClick ? "button" : undefined} tabIndex={onClick ? 0 : undefined}
          onKeyDown={onClick ? (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onClick(); } } : undefined}>
          <div className="wes-between"><span className="op">{o.operation}</span>{dot === "running" && <Thinking />}</div>
          <div className="ow">{o.owner}{o.note ? ` · ${o.note}` : ""}</div>
        </div>
      )) : <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)", padding: "4px 0 8px" }}>{empty ?? "None."}</div>}
    </div>
  );
}

/* ---------------- executive autonomy ---------------- */
function ExecutiveAutonomy() {
  const [d, setD] = useState<OpAutonomy | null>(null);
  useEffect(() => { founderApi.opAutonomy().then(setD).catch(() => {}); }, []);
  if (!d) return null;
  return (
    <section className="wes-in">
      <div className="wes-h3" style={{ marginBottom: 14 }}>Executive Autonomy</div>
      <div className="wes-score">
        {d.executives.map((e) => (
          <div key={e.executive} className="wes-score-card">
            <div style={{ fontWeight: 620, fontSize: "var(--wes-fs-sm)" }}>{e.executive}</div>
            <div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>Now: {e.current_initiative}</div>
            <div className="wes-row" style={{ gap: 8, flexWrap: "wrap" }}>
              {e.delegated_work > 0 && <Badge tone="info">{e.delegated_work} delegated</Badge>}
              <Badge tone={e.completed_work === "Active" ? "ok" : "neutral"}>{e.completed_work}</Badge>
            </div>
            {e.recommendations.length > 0 && <div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)", lineHeight: 1.4 }}>↳ {e.recommendations[0]}</div>}
          </div>
        ))}
      </div>
    </section>
  );
}

/* ---------------- autonomous decisions ---------------- */
function DecisionsView({ decisions, onOpen }: { decisions: OpDecisions | null; onOpen: () => void }) {
  if (!decisions) return <Card><Skeleton h={160} /></Card>;
  return (
    <div className="wes-in wes-stack">
      <div className="wes-grid cols-3">
        <Stat n={decisions.company_level} k="Company decided" />
        <Stat n={decisions.board_level} k="Board decided" />
        <Stat n={decisions.founder_level} k="Awaiting you" tone="warn" />
      </div>
      <Card>
        <div className="wes-h3" style={{ marginBottom: 14 }}>Recent decisions the company made for you</div>
        {decisions.recent.map((x, i) => (
          <div key={i} className="wes-know-item">
            <div className="wes-between"><span style={{ fontWeight: 560, fontSize: "var(--wes-fs-sm)" }}>{x.decision}</span><Badge tone="ok">{x.approval_policy}</Badge></div>
            <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)", marginTop: 4 }}>{x.reason}</div>
            <div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)", marginTop: 3 }}>{x.made_by} · {x.confidence}% confident · {x.business_impact}</div>
          </div>
        ))}
      </Card>
      {decisions.founder_level > 0 && (
        <Card>
          <div className="wes-between"><div><div className="wes-h3">Your decisions</div><div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)", marginTop: 4 }}>{decisions.founder_level} strategic decision{decisions.founder_level !== 1 ? "s" : ""} need you.</div></div>
            <button className="wes-btn wes-btn-primary wes-btn-sm" onClick={onOpen}>Open decision queue →</button></div>
        </Card>
      )}
    </div>
  );
}

/* ---------------- approval policy ---------------- */
function PolicyView() {
  const [d, setD] = useState<OpPolicy | null>(null);
  const [pol, setPol] = useState<OpPolicies | null>(null);
  useEffect(() => { founderApi.opPolicy().then(setD).catch(() => {}); founderApi.opPolicies().then(setPol).catch(() => {}); }, []);
  if (!d) return <Card><Skeleton h={200} /></Card>;
  return (
    <div className="wes-in wes-stack">
      <div>
        <div className="wes-h3" style={{ marginBottom: 14 }}>Who decides what</div>
        {d.levels.map((l) => (
          <div key={l.level} className={`wes-policy-lvl l${l.level}`}>
            <div className="wes-row" style={{ gap: 12, marginBottom: 8 }}>
              <div className="wes-lvl-badge">{l.level}</div>
              <div><div style={{ fontWeight: 640 }}>{l.name}</div><div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>{l.why}</div></div>
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 4 }}>
              {l.scope.map((s, i) => <span key={i} className="wes-chip-sm">{s}</span>)}
            </div>
          </div>
        ))}
      </div>
      {pol && (
        <Card>
          <div className="wes-h3" style={{ marginBottom: 14 }}>Company Policies</div>
          {pol.policies.map((p, i) => (
            <div key={i} className="wes-know-item"><div className="wes-between"><span style={{ fontWeight: 560, fontSize: "var(--wes-fs-sm)" }}>{p.policy}</span><span className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>{p.owner}</span></div>
              <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)", marginTop: 3 }}>{p.rule}</div></div>
          ))}
        </Card>
      )}
    </div>
  );
}

/* ---------------- escalations ---------------- */
function EscalationsView({ onOpen }: { onOpen: () => void }) {
  const [d, setD] = useState<OpEscalations | null>(null);
  useEffect(() => { founderApi.opEscalations().then(setD).catch(() => {}); }, []);
  if (!d) return <Card><Skeleton h={160} /></Card>;
  if (!d.escalations.length) return <Card><Empty icon="✓" title="Nothing escalated" hint="The company is handling everything within policy." /></Card>;
  return (
    <Card className="wes-in">
      <div className="wes-h3" style={{ marginBottom: 8 }}>Escalation Center</div>
      <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)", marginBottom: 14 }}>{d.total} item{d.total !== 1 ? "s" : ""} rose above autonomous handling.</div>
      {d.escalations.map((e, i) => (
        <div key={i} className="wes-att-row" style={{ marginBottom: 8 }}>
          <span className={`wes-att-dot ${e.severity}`} />
          <div style={{ flex: 1 }}><div style={{ fontSize: "var(--wes-fs-sm)" }}>{e.text}</div><div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>{e.type} · {e.owner}</div></div>
          {e.type.includes("Founder") && <button className="wes-btn wes-btn-ghost wes-btn-sm" onClick={onOpen}>Review</button>}
        </div>
      ))}
    </Card>
  );
}

/* ---------------- automation ---------------- */
function AutomationView() {
  const [d, setD] = useState<OpAutomation | null>(null);
  useEffect(() => { founderApi.opAutomation().then(setD).catch(() => {}); }, []);
  if (!d) return <Card><Skeleton h={160} /></Card>;
  const max = Math.max(...d.automated_processes.map((p) => p.runs), 1);
  return (
    <div className="wes-grid cols-2 wes-in">
      <Card>
        <div className="wes-h3" style={{ marginBottom: 6 }}>Time saved</div>
        <div className="wes-h1" style={{ margin: "4px 0" }}>~{d.time_saved_hours}h</div>
        <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)" }}>{d.manual_work_eliminated}</div>
        <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)", marginTop: 12 }}>{d.business_impact}</div>
        <div style={{ marginTop: 12 }}><Badge tone="ok" dot>{d.automation_confidence}% confidence</Badge></div>
      </Card>
      <Card>
        <div className="wes-h3" style={{ marginBottom: 14 }}>Processes now automated</div>
        {d.automated_processes.map((p, i) => (
          <div key={i} className="wes-reuse-row">
            <div style={{ flex: 1 }}><div style={{ fontSize: "var(--wes-fs-sm)" }}>{p.process}</div><div className="wes-reuse-bar" style={{ width: `${(p.runs / max) * 100}%`, marginTop: 6 }} /></div>
            <span className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>{p.runs} runs</span>
          </div>
        ))}
      </Card>
    </div>
  );
}

/* ---------------- trust ---------------- */
function TrustView() {
  const [d, setD] = useState<OpTrust | null>(null);
  useEffect(() => { founderApi.opTrust().then(setD).catch(() => {}); }, []);
  if (!d) return <Card><Skeleton h={160} /></Card>;
  return (
    <div className="wes-in wes-stack">
      <div className="wes-trust">
        <Card><div className="wes-between"><div><div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)" }}>Executive accuracy</div><div className="wes-h1">{d.executive_accuracy}%</div></div><ProgressRing value={d.executive_accuracy} /></div></Card>
        <Card><div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)" }}>Autonomous decisions</div><div className="wes-h1">{d.autonomous_decisions}</div><div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>run without you</div></Card>
        <Card><div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)" }}>Your overrides</div><div className="wes-h1">{d.founder_overrides}</div><div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>times you stepped in</div></Card>
      </div>
      <Card>
        <div className="wes-h3" style={{ marginBottom: 12 }}>Founder Controls</div>
        <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)", marginBottom: 12 }}>You govern the company — you never execute technical work. {d.note}</div>
        <div className="wes-controls">
          {FOUNDER_CONTROLS.map((c) => <button key={c} className={`wes-btn ${c === "Approve" ? "wes-btn-primary" : "wes-btn-ghost"} wes-btn-sm`} onClick={() => { if (c === "Approve") window.location.href = "/command"; }}>{c}</button>)}
        </div>
        <div className="wes-row" style={{ gap: 16, marginTop: 16 }}>
          <span className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)" }}>Decision confidence: <strong style={{ color: "var(--wes-text)" }}>{d.decision_confidence}%</strong></span>
          <span className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)" }}>Learning: <strong style={{ color: "var(--wes-ok)" }}>{d.learning_trend}</strong></span>
          {d.evolution_score != null && <Badge tone="info">Evolution {d.evolution_score}</Badge>}
        </div>
      </Card>
    </div>
  );
}

function Stat({ n, k, tone }: { n: number; k: string; tone?: "warn" }) {
  return <div className="wes-op-stat"><div className="n" style={{ color: tone === "warn" && n ? "var(--wes-warn)" : undefined }}>{n}</div><div className="k">{k}</div></div>;
}

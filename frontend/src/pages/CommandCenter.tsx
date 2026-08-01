import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  founderApi, type BrainSearch, type CmdBrief, type CmdDecisions, type CmdHealth,
  type CmdOpportunities, type CmdOverview, type CmdPredictions, type CmdRisks, type CmdScoreboard,
} from "../api/founder";
import { Badge, Card, Empty, Skeleton, Thinking, healthTone } from "../components/ui/kit";

type Tab = "command" | "scoreboard" | "decisions" | "predictions" | "health" | "risks" | "opportunities";
const initials = (s: string) => s.replace(/^AI /, "").split(" ").map((w) => w[0]).slice(0, 2).join("").toUpperCase();

const KPI_ORDER: [string, string][] = [
  ["company_health", "Company health"], ["mission_health", "Mission health"],
  ["execution_velocity", "Execution"], ["decision_queue", "Decisions"],
  ["knowledge_growth", "Knowledge"], ["workforce_utilisation", "Workforce"],
  ["executive_confidence", "Confidence"], ["learning_trend", "Learning"],
  ["business_risk", "Risk"], ["strategic_momentum", "Momentum"],
];

export function CommandCenter() {
  const navigate = useNavigate();
  const [ov, setOv] = useState<CmdOverview | null>(null);
  const [brief, setBrief] = useState<CmdBrief | null>(null);
  const [tab, setTab] = useState<Tab>("command");

  useEffect(() => {
    const load = () => { founderApi.cmdOverview().then(setOv).catch(() => {}); founderApi.cmdBrief().then(setBrief).catch(() => {}); };
    load();
    const iv = setInterval(load, 20000);
    return () => clearInterval(iv);
  }, []);

  return (
    <div className="wes-page wes-stack">
      {/* Daily brief hero */}
      <section className="wes-brain-hero wes-in wes-in-1">
        <div className="wes-eyebrow" style={{ marginBottom: 8 }}>Founder Command Center</div>
        {brief ? (
          <>
            <h1 className="wes-h1">{brief.greeting} Here's your company.</h1>
            <div className="wes-brief-cols">
              <div>
                <div className="wes-rail-k" style={{ marginBottom: 8 }}>Since you were last here</div>
                <ul style={{ margin: 0, paddingLeft: 16, color: "var(--wes-text-2)", fontSize: "var(--wes-fs-sm)", lineHeight: 1.7 }}>
                  {brief.yesterday.map((x, i) => <li key={i}>{x}</li>)}
                </ul>
              </div>
              <div>
                <div className="wes-rail-k" style={{ marginBottom: 8 }}>Today's priorities</div>
                <ul style={{ margin: 0, paddingLeft: 16, color: "var(--wes-text)", fontSize: "var(--wes-fs-sm)", lineHeight: 1.7 }}>
                  {brief.today_priorities.map((x, i) => <li key={i}>{x}</li>)}
                </ul>
              </div>
            </div>
            <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)", marginTop: 16 }}>✦ {brief.closing}</div>
          </>
        ) : <Skeleton h={120} />}
      </section>

      <CmdSearch />

      {/* headline KPIs */}
      {ov ? (
        <section className="wes-cmd-kpis wes-in wes-in-2">
          {KPI_ORDER.map(([key, label]) => {
            const k = ov.kpis[key];
            return (
              <div key={key} className="wes-kpi">
                <div className="n">{k?.value ?? "—"}<span className={`wes-trend ${k?.trend}`}>{arrow(k?.trend)}</span></div>
                <div className="k">{label}</div>
                <div className="s">{k?.label}</div>
              </div>
            );
          })}
        </section>
      ) : <div className="wes-cmd-kpis">{Array.from({ length: 5 }).map((_, i) => <Card key={i}><Skeleton h={44} /></Card>)}</div>}

      {/* needs attention */}
      {ov && ov.attention.length > 0 && (
        <section className="wes-in wes-in-3">
          <div className="wes-h3" style={{ marginBottom: 12 }}>Needs your attention</div>
          <div className="wes-attention">
            {ov.attention.map((a, i) => (
              <div key={i} className="wes-att-row">
                <span className={`wes-att-dot ${a.urgency}`} />
                <span style={{ fontSize: "var(--wes-fs-sm)" }}>{a.text}</span>
                {a.kind === "decision" && <button className="wes-btn wes-btn-ghost wes-btn-sm" style={{ marginLeft: "auto" }} onClick={() => setTab("decisions")}>Open queue</button>}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* tabs */}
      <div className="wes-seg-nav wes-in wes-in-4" style={{ flexWrap: "wrap" }}>
        {([["command", "Command"], ["scoreboard", "Executives"], ["decisions", "Decisions"], ["predictions", "Predictions"], ["health", "Health"], ["risks", "Risks"], ["opportunities", "Opportunities"]] as const).map(([v, l]) => (
          <button key={v} className={`wes-seg-btn${tab === v ? " active" : ""}`} onClick={() => setTab(v)}>{l}</button>
        ))}
      </div>

      {tab === "command" && <CommandView />}
      {tab === "scoreboard" && <ScoreboardView />}
      {tab === "decisions" && <DecisionsView onOpen={(id) => id && navigate(`/missions/${id}`)} />}
      {tab === "predictions" && <PredictionsView />}
      {tab === "health" && <HealthView />}
      {tab === "risks" && <RisksView />}
      {tab === "opportunities" && <OpportunitiesView />}
    </div>
  );
}

/* ---------------- command (timeline + BI) ---------------- */
function CommandView() {
  const [tl, setTl] = useState<{ events: { headline: string; kind: string }[] } | null>(null);
  const [bi, setBi] = useState<{ kpis: { kpi: string; value: number | null; unit: string }[] } | null>(null);
  const [perf, setPerf] = useState<{ forecast: string; completion_rate: number; blocked_missions: number } | null>(null);
  useEffect(() => {
    founderApi.cmdTimeline().then(setTl).catch(() => {});
    founderApi.cmdBI().then(setBi).catch(() => {});
    founderApi.cmdMissionPerformance().then(setPerf).catch(() => {});
  }, []);
  return (
    <div className="wes-grid cols-2 wes-in">
      <Card>
        <div className="wes-h3" style={{ marginBottom: 16 }}>Company Timeline</div>
        {tl ? (
          <div className="wes-timeline">
            {tl.events.map((e, i) => <div key={i} className={`wes-tl-item${e.kind === "delivery" ? " done" : ""}`}><div style={{ fontSize: "var(--wes-fs-sm)", fontWeight: 520 }}>{e.headline}</div></div>)}
          </div>
        ) : <Skeleton h={160} />}
      </Card>
      <div className="wes-stack">
        <Card>
          <div className="wes-h3" style={{ marginBottom: 14 }}>Business Intelligence</div>
          {bi ? (
            <div className="wes-grid cols-2" style={{ gap: 12 }}>
              {bi.kpis.map((k, i) => (
                <div key={i}><div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)", textTransform: "uppercase", letterSpacing: ".08em" }}>{k.kpi}</div>
                  <div style={{ fontWeight: 680, fontSize: "1.1rem" }}>{k.value ?? "—"} <span className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>{k.unit}</span></div></div>
              ))}
            </div>
          ) : <Skeleton h={100} />}
        </Card>
        {perf && (
          <Card>
            <div className="wes-h3" style={{ marginBottom: 10 }}>Mission forecast</div>
            <p className="wes-muted" style={{ fontSize: "var(--wes-fs-sm)" }}>{perf.forecast}</p>
            <div className="wes-row" style={{ gap: 16, marginTop: 12 }}>
              <span className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)" }}>Completion {perf.completion_rate}%</span>
              {perf.blocked_missions > 0 && <Badge tone="warn">{perf.blocked_missions} early-stage</Badge>}
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}

/* ---------------- scoreboard ---------------- */
function ScoreboardView() {
  const [d, setD] = useState<CmdScoreboard | null>(null);
  useEffect(() => { founderApi.cmdScoreboard().then(setD).catch(() => {}); }, []);
  if (!d) return <Card><Skeleton h={160} /></Card>;
  return (
    <div className="wes-score wes-in">
      {d.executives.map((e) => (
        <div key={e.executive} className="wes-score-card">
          <div className="wes-score-head">
            <div className="wes-row" style={{ gap: 10 }}>
              <div className="wes-person-av" style={{ width: 36, height: 36, borderRadius: 11, background: e.workload ? "var(--wes-accent-grad)" : "var(--wes-bg-4)", color: e.workload ? "#0b0d14" : "var(--wes-text-3)", fontSize: ".7rem" }}>{initials(e.executive)}</div>
              <div><div style={{ fontWeight: 620, fontSize: "var(--wes-fs-sm)" }}>{e.executive}</div><div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>{e.confidence}% confident</div></div>
            </div>
            <Badge tone={healthTone(e.health)}>{e.health}</Badge>
          </div>
          <div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>{e.responsibility}</div>
          <div className="wes-between">
            <div className="wes-score-load">{Array.from({ length: 5 }).map((_, i) => <i key={i} className={i < e.workload ? "on" : ""} />)}</div>
            <span className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>{e.workload} mission{e.workload !== 1 ? "s" : ""}{e.pending_decisions ? ` · ${e.pending_decisions} decisions` : ""}</span>
          </div>
          {e.mission_ownership.length > 0 && <div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)", lineHeight: 1.4 }}>{e.mission_ownership.join(" · ").slice(0, 90)}</div>}
        </div>
      ))}
    </div>
  );
}

/* ---------------- decisions ---------------- */
function DecisionsView({ onOpen }: { onOpen: (id: string | null) => void }) {
  const [d, setD] = useState<CmdDecisions | null>(null);
  useEffect(() => { founderApi.cmdDecisions().then(setD).catch(() => {}); }, []);
  if (!d) return <Card><Skeleton h={160} /></Card>;
  if (!d.decisions.length) return <Card><Empty icon="✓" title="You're all caught up" hint="No decisions need you right now." /></Card>;
  return (
    <div className="wes-in">
      <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)", marginBottom: 14 }}>{d.total} decision{d.total !== 1 ? "s" : ""} in your queue — act from here.</div>
      {d.decisions.slice(0, 12).map((x, i) => (
        <div key={i} className="wes-dc">
          <div className="wes-between" style={{ gap: 12, flexWrap: "wrap" }}>
            <div style={{ minWidth: 220, flex: 1 }}>
              <div className="wes-row" style={{ marginBottom: 6 }}><Badge tone={x.urgency === "high" ? "risk" : "info"}>{x.urgency}</Badge></div>
              <div style={{ fontWeight: 580 }}>{x.title}</div>
              <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)", marginTop: 4 }}>{x.recommendation}</div>
              <div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)", marginTop: 6 }}>Outcome: {x.expected_outcome}</div>
            </div>
          </div>
          <div className="wes-dc-actions">
            <button className="wes-btn wes-btn-ok wes-btn-sm" onClick={() => onOpen(x.id)}>Approve</button>
            <button className="wes-btn wes-btn-ghost wes-btn-sm" onClick={() => onOpen(x.id)}>Review</button>
            <button className="wes-btn wes-btn-quiet wes-btn-sm" onClick={() => onOpen(x.id)}>Discuss</button>
            <button className="wes-btn wes-btn-quiet wes-btn-sm">Delegate</button>
            <button className="wes-btn wes-btn-quiet wes-btn-sm">Schedule Later</button>
          </div>
        </div>
      ))}
    </div>
  );
}

/* ---------------- predictions ---------------- */
function PredictionsView() {
  const [d, setD] = useState<CmdPredictions | null>(null);
  useEffect(() => { founderApi.cmdPredictions().then(setD).catch(() => {}); }, []);
  if (!d) return <Card><Skeleton h={160} /></Card>;
  return (
    <Card className="wes-in">
      <div className="wes-h3" style={{ marginBottom: 8 }}>What's likely to happen next</div>
      <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)", marginBottom: 8 }}>Composed from real company signals — each with a confidence.</div>
      {d.insights.map((p, i) => (
        <div key={i} className="wes-pred">
          <span className="wes-live-dot" style={{ marginTop: 5 }} />
          <div style={{ flex: 1 }}><div style={{ fontSize: "var(--wes-fs-sm)" }}>{p.prediction}</div><div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)", marginTop: 2 }}>{p.type.replace(/_/g, " ")}</div></div>
          <span className="wes-pred-conf">{p.confidence}%</span>
        </div>
      ))}
    </Card>
  );
}

/* ---------------- health ---------------- */
function HealthView() {
  const [d, setD] = useState<CmdHealth | null>(null);
  useEffect(() => { founderApi.cmdHealth().then(setD).catch(() => {}); }, []);
  if (!d) return <Card><Skeleton h={200} /></Card>;
  return (
    <div className="wes-in wes-stack">
      <Card>
        <div className="wes-between" style={{ marginBottom: 16 }}><div className="wes-h3">Company Health · {d.overall}</div><Badge tone={healthTone(d.overall)}>{d.score}%</Badge></div>
        <div className="wes-areas">
          {d.areas.map((a) => (
            <div key={a.area} className="wes-area-row">
              <div style={{ width: 130 }}><div style={{ fontWeight: 560, fontSize: "var(--wes-fs-sm)" }}>{a.area}</div><div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>{a.owner}</div></div>
              <div className="wes-area-bar"><span style={{ width: `${a.confidence}%`, background: a.health === "healthy" ? "var(--wes-ok)" : "var(--wes-warn)" }} /></div>
              <Badge tone={healthTone(a.health)}>{a.health}</Badge>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

/* ---------------- risks ---------------- */
function RisksView() {
  const [d, setD] = useState<CmdRisks | null>(null);
  useEffect(() => { founderApi.cmdRisks().then(setD).catch(() => {}); }, []);
  if (!d) return <Card><Skeleton h={200} /></Card>;
  return (
    <div className="wes-in">
      <div className="wes-row" style={{ gap: 8, marginBottom: 14, flexWrap: "wrap" }}>
        {d.by_category.map((c) => <span key={c.category} className="wes-chip-sm">{c.category}: {c.count}</span>)}
      </div>
      <Card>
        {d.risks.length ? d.risks.map((r, i) => (
          <div key={i} className="wes-risk-row">
            <div><div style={{ fontWeight: 540, fontSize: "var(--wes-fs-sm)" }}>{r.risk}</div>
              <div className="wes-risk-meta"><span className="wes-chip-sm">{r.category}</span><span className="wes-chip-sm">Owner: {r.owner}</span></div>
              <div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)", marginTop: 6 }}>{r.mitigation}</div></div>
            <span className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>{r.confidence}%</span>
          </div>
        )) : <Empty title="No open risks" />}
      </Card>
    </div>
  );
}

/* ---------------- opportunities ---------------- */
function OpportunitiesView() {
  const [d, setD] = useState<CmdOpportunities | null>(null);
  useEffect(() => { founderApi.cmdOpportunities().then(setD).catch(() => {}); }, []);
  if (!d) return <Card><Skeleton h={200} /></Card>;
  return (
    <div className="wes-grid cols-2 wes-in">
      <Card>
        <div className="wes-h3" style={{ marginBottom: 12 }}>High-value improvements</div>
        {d.high_value_improvements.map((o, i) => (
          <div key={i} className="wes-know-item">
            <div className="wes-between"><span style={{ fontSize: "var(--wes-fs-sm)", fontWeight: 540 }}>{o.title}</span>{o.approval && <Badge tone="warn">Approval</Badge>}</div>
            {o.value && <div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)", marginTop: 3 }}>{o.value}</div>}
          </div>
        ))}
      </Card>
      <div className="wes-stack">
        {d.reuse_rate != null && (
          <Card><div className="wes-h3" style={{ marginBottom: 6 }}>Reuse leverage</div>
            <div className="wes-h1">{d.reuse_rate}%</div><div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)" }}>of knowledge is already being reused</div></Card>
        )}
        {d.future_hiring.length > 0 && (
          <Card>
            <div className="wes-h3" style={{ marginBottom: 12 }}>Recommended future roles</div>
            {d.future_hiring.map((h, i) => <div key={i} className="wes-know-item"><div style={{ fontWeight: 560, fontSize: "var(--wes-fs-sm)" }}>{h.role}</div><div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>{h.value}</div></div>)}
          </Card>
        )}
      </div>
    </div>
  );
}

/* ---------------- search ---------------- */
function CmdSearch() {
  const [q, setQ] = useState(""); const [res, setRes] = useState<BrainSearch | null>(null); const [busy, setBusy] = useState(false);
  const t = useRef<number | undefined>(undefined);
  function run(v: string) {
    setQ(v); window.clearTimeout(t.current);
    if (v.trim().length < 3) { setRes(null); return; }
    t.current = window.setTimeout(async () => { setBusy(true); try { setRes(await founderApi.cmdSearch(v)); } finally { setBusy(false); } }, 350);
  }
  return (
    <section className="wes-in wes-in-2">
      <div className="wes-search-box"><span className="wes-dim">⌕</span>
        <input placeholder="Search missions, executives, knowledge, risks, decisions…" value={q} onChange={(e) => run(e.target.value)} />{busy && <Thinking />}</div>
      {res && res.total > 0 && (
        <div className="wes-search-group">
          {g("Missions", res.results.missions.map((x) => x.title))}
          {g("Knowledge", res.results.knowledge.map((x) => x.title))}
          {g("Recommendations", res.results.recommendations.map((x) => x.title))}
        </div>
      )}
    </section>
  );
  function g(label: string, items: string[]) {
    if (!items.length) return null;
    return <div style={{ marginBottom: 14 }}><div className="wes-rail-k" style={{ marginBottom: 8 }}>{label}</div>{items.slice(0, 5).map((x, i) => <div key={i} className="wes-search-item">{x}</div>)}</div>;
  }
}

function arrow(trend?: string) { return trend === "up" ? "↑" : trend === "watch" ? "⚠" : ""; }

import { useEffect, useMemo, useRef, useState } from "react";

import {
  founderApi, type BrainSearch, type KnowledgeCollab, type KnowledgeGraph,
  type KnowledgeHome, type KnowledgeInsights, type KnowledgeMemory, type KnowledgeReuse,
} from "../api/founder";
import { Badge, Card, Empty, Skeleton, Thinking } from "../components/ui/kit";

type Tab = "overview" | "timeline" | "memory" | "reuse" | "graph" | "collab" | "insights";

export function KnowledgeNetwork() {
  const [home, setHome] = useState<KnowledgeHome | null>(null);
  const [tab, setTab] = useState<Tab>("overview");

  useEffect(() => {
    const load = () => founderApi.knHome().then(setHome).catch(() => {});
    load();
    const iv = setInterval(load, 20000);
    return () => clearInterval(iv);
  }, []);

  const m = home?.metrics;
  return (
    <div className="wes-page wes-stack">
      <section className="wes-brain-hero wes-in wes-in-1">
        <div className="wes-eyebrow" style={{ marginBottom: 8 }}>Knowledge Network</div>
        <h1 className="wes-h1">Your company is getting smarter.</h1>
        <p className="wes-dim" style={{ marginTop: 6 }}>What it knows, how it learned it, where it's reused — and what's becoming obsolete.</p>
        {m && (
          <div className="wes-row" style={{ marginTop: 20, gap: 14, flexWrap: "wrap" }}>
            <Badge tone={m.knowledge_health === "strong" ? "ok" : "info"} dot>Knowledge {m.knowledge_health}</Badge>
            <span className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)" }}>Learning trend: {m.trend}</span>
            {home?.fastest_growing_domain && <Badge tone="info">Fastest: {home.fastest_growing_domain.domain}</Badge>}
          </div>
        )}
      </section>

      <KnSearch />

      {!m ? <div className="wes-kmetrics">{Array.from({ length: 6 }).map((_, i) => <Card key={i}><Skeleton h={44} /></Card>)}</div> : (
        <section className="wes-kmetrics wes-in wes-in-2">
          <Metric n={m.total_knowledge} k="Knowledge" s="items owned" />
          <Metric n={`+${m.growth_7d}`} k="Growth" s="this week" />
          <Metric n={m.coverage_areas} k="Coverage" s="areas" />
          <Metric n={`${m.confidence}%`} k="Confidence" s={m.quality} />
          <Metric n={`${m.reuse_rate}%`} k="Reuse" s="knowledge reused" />
          <Metric n={`${m.freshness}%`} k="Freshness" s={`${m.ageing} ageing`} />
        </section>
      )}

      <div className="wes-seg-nav wes-in wes-in-3" style={{ flexWrap: "wrap" }}>
        {([["overview", "Overview"], ["timeline", "Timeline"], ["memory", "Organisational Memory"], ["reuse", "Reuse"], ["graph", "Graph"], ["collab", "Collaboration"], ["insights", "Insights"]] as const).map(([v, l]) => (
          <button key={v} className={`wes-seg-btn${tab === v ? " active" : ""}`} onClick={() => setTab(v)}>{l}</button>
        ))}
      </div>

      {tab === "overview" && home && <Overview home={home} />}
      {tab === "timeline" && <TimelineView />}
      {tab === "memory" && <MemoryView />}
      {tab === "reuse" && <ReuseView />}
      {tab === "graph" && <GraphView />}
      {tab === "collab" && <CollabView />}
      {tab === "insights" && <InsightsView />}
    </div>
  );
}

/* ---------------- overview ---------------- */
function Overview({ home }: { home: KnowledgeHome }) {
  return (
    <div className="wes-grid cols-2 wes-in">
      <Card>
        <div className="wes-h3" style={{ marginBottom: 12 }}>Learned recently</div>
        {home.recent_learnings.map((x, i) => (
          <div key={i} className="wes-know-item">
            <div style={{ fontSize: "var(--wes-fs-sm)", lineHeight: 1.5 }}>{x.headline}</div>
            <div className="wes-row" style={{ gap: 8, marginTop: 5 }}><span className="wes-chip-sm">{x.area}</span><span className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>{x.confidence}% confident</span></div>
          </div>
        ))}
      </Card>
      <div className="wes-stack">
        <Card>
          <div className="wes-h3" style={{ marginBottom: 12 }}>Most valuable knowledge</div>
          {home.most_valuable.map((x, i) => (
            <div key={i} className="wes-between wes-know-item">
              <span style={{ fontSize: "var(--wes-fs-sm)" }}>{x.title}</span>
              <Badge tone="info">{x.value}</Badge>
            </div>
          ))}
        </Card>
        <Card>
          <div className="wes-h3" style={{ marginBottom: 12 }}>Missions that taught us most</div>
          {home.contributing_missions.map((x, i) => (
            <div key={i} className="wes-between" style={{ marginBottom: 8 }}><span style={{ fontSize: "var(--wes-fs-sm)" }}>{x.mission}</span><span className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>{x.learnings} learnings</span></div>
          ))}
        </Card>
      </div>
    </div>
  );
}

/* ---------------- timeline ---------------- */
function TimelineView() {
  const [d, setD] = useState<{ events: { headline: string; area: string; by: string; confidence: number }[] } | null>(null);
  useEffect(() => { founderApi.knTimeline().then(setD).catch(() => {}); }, []);
  if (!d) return <Card><Skeleton h={200} /></Card>;
  return (
    <Card className="wes-in">
      <div className="wes-h3" style={{ marginBottom: 18 }}>How the company learned</div>
      <div className="wes-timeline">
        {d.events.map((e, i) => (
          <div key={i} className="wes-tl-item done">
            <div style={{ fontWeight: 540, fontSize: "var(--wes-fs-sm)" }}>{e.headline}</div>
            <div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)", marginTop: 3 }}>{e.area} · by {e.by} · {e.confidence}% confident</div>
          </div>
        ))}
      </div>
    </Card>
  );
}

/* ---------------- organisational memory ---------------- */
function MemoryView() {
  const [d, setD] = useState<KnowledgeMemory | null>(null);
  useEffect(() => { founderApi.knMemory().then(setD).catch(() => {}); }, []);
  if (!d) return <Card><Skeleton h={200} /></Card>;
  return (
    <div className="wes-grid cols-2 wes-in">
      <Card>
        <div className="wes-h3" style={{ marginBottom: 12 }}>Repeated patterns</div>
        {d.repeated_patterns.length ? d.repeated_patterns.map((p, i) => (
          <div key={i} className="wes-between wes-know-item"><span style={{ fontSize: "var(--wes-fs-sm)" }}>{p.pattern}</span><Badge tone="info">seen {p.seen}×</Badge></div>
        )) : <Empty title="Patterns emerging" />}
        <div className="wes-h3" style={{ margin: "18px 0 12px" }}>Mistakes now avoided</div>
        <ul style={{ margin: 0, paddingLeft: 16, color: "var(--wes-text-2)", fontSize: "var(--wes-fs-sm)", lineHeight: 1.6 }}>
          {d.mistakes_avoided.map((x, i) => <li key={i}>{x}</li>)}
        </ul>
      </Card>
      <div className="wes-stack">
        <Card>
          <div className="wes-h3" style={{ marginBottom: 12 }}>Lessons remembered</div>
          <ul style={{ margin: 0, paddingLeft: 16, color: "var(--wes-text-2)", fontSize: "var(--wes-fs-sm)", lineHeight: 1.6 }}>
            {d.lessons_remembered.map((x, i) => <li key={i}>{x}</li>)}
          </ul>
        </Card>
        <Card>
          <div className="wes-between" style={{ marginBottom: 10 }}><div className="wes-h3">Ageing knowledge</div><Badge tone="warn">{d.ageing.stale_count} ageing</Badge></div>
          {d.ageing.stale_examples.length ? d.ageing.stale_examples.map((x, i) => <div key={i} className="wes-know-item" style={{ fontSize: "var(--wes-fs-sm)", color: "var(--wes-text-3)" }}>{x}</div>) : <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)" }}>Everything is fresh.</div>}
        </Card>
      </div>
    </div>
  );
}

/* ---------------- reuse ---------------- */
function ReuseView() {
  const [d, setD] = useState<KnowledgeReuse | null>(null);
  useEffect(() => { founderApi.knReuse().then(setD).catch(() => {}); }, []);
  if (!d) return <Card><Skeleton h={200} /></Card>;
  const max = Math.max(...d.frequently_reused.map((r) => r.used), 1);
  return (
    <div className="wes-grid cols-2 wes-in">
      <Card>
        <div className="wes-between" style={{ marginBottom: 12 }}><div className="wes-h3">Most reused knowledge</div><Badge tone="ok">{d.reuse_rate}% reuse</Badge></div>
        {d.frequently_reused.map((r, i) => (
          <div key={i} className="wes-reuse-row">
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: "var(--wes-fs-sm)" }}>{r.knowledge}</div>
              <div className="wes-reuse-bar" style={{ width: `${(r.used / max) * 100}%`, marginTop: 6 }} />
            </div>
            <span className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>used {r.used}×</span>
          </div>
        ))}
      </Card>
      <div className="wes-stack">
        <Card>
          <div className="wes-h3" style={{ marginBottom: 12 }}>Recommended consolidation</div>
          {d.recommended_consolidation.length ? d.recommended_consolidation.map((x, i) => <div key={i} className="wes-search-item">{x}</div>) : <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)" }}>No duplication detected.</div>}
        </Card>
        <Card>
          <div className="wes-h3" style={{ marginBottom: 12 }}>Not yet reused</div>
          {d.never_reused.length ? <ul style={{ margin: 0, paddingLeft: 16, color: "var(--wes-text-2)", fontSize: "var(--wes-fs-sm)", lineHeight: 1.6 }}>{d.never_reused.map((x, i) => <li key={i}>{x}</li>)}</ul> : <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)" }}>All knowledge is being applied.</div>}
        </Card>
      </div>
    </div>
  );
}

/* ---------------- graph ---------------- */
function GraphView() {
  const [d, setD] = useState<KnowledgeGraph | null>(null);
  useEffect(() => { founderApi.knGraph().then(setD).catch(() => {}); }, []);
  const pos = useMemo(() => {
    const p: Record<string, { x: number; y: number }> = { company: { x: 260, y: 210 } };
    const others = (d?.nodes ?? []).filter((n) => n.id !== "company");
    others.forEach((n, i) => { const a = (i / Math.max(others.length, 1)) * Math.PI * 2 - Math.PI / 2; const r = i % 2 ? 120 : 180; p[n.id] = { x: 260 + Math.cos(a) * r, y: 210 + Math.sin(a) * r }; });
    return p;
  }, [d]);
  const colors: Record<string, string> = { company: "#8b6dff", knowledge: "#f5b544", department: "#6d8bff", executive: "#43d9c7", blueprint: "#a8b0c4", recommendation: "#37d39b" };
  if (!d) return <Card><Skeleton h={300} /></Card>;
  return (
    <Card className="wes-in">
      <div className="wes-h3" style={{ marginBottom: 14 }}>Knowledge Graph</div>
      <svg className="wes-graph" viewBox="0 0 520 420" preserveAspectRatio="xMidYMid meet">
        {d.edges.map((e, i) => { const a = pos[e.from], b = pos[e.to]; if (!a || !b) return null; return <line key={i} className="lnk" x1={a.x} y1={a.y} x2={b.x} y2={b.y} />; })}
        {d.nodes.map((n) => { const pt = pos[n.id]; if (!pt) return null; const isC = n.group === "company";
          return <g key={n.id} className="node" transform={`translate(${pt.x},${pt.y})`}><circle r={isC ? 12 : 6} fill={colors[n.group] ?? "#6d8bff"} /><text x={isC ? 0 : 10} y={isC ? 26 : 3} textAnchor={isC ? "middle" : "start"}>{n.label}</text></g>; })}
      </svg>
    </Card>
  );
}

/* ---------------- collaboration ---------------- */
function CollabView() {
  const [d, setD] = useState<KnowledgeCollab | null>(null);
  useEffect(() => { founderApi.knCollaboration().then(setD).catch(() => {}); }, []);
  if (!d) return <Card><Skeleton h={200} /></Card>;
  const max = Math.max(...d.contributions.map((c) => c.knowledge), 1);
  return (
    <div className="wes-grid cols-2 wes-in">
      <Card>
        <div className="wes-h3" style={{ marginBottom: 14 }}>Who creates knowledge</div>
        {d.contributions.map((c, i) => (
          <div key={i} className="wes-reuse-row">
            <div style={{ flex: 1 }}><div style={{ fontSize: "var(--wes-fs-sm)" }}>{c.contributor}</div><div className="wes-reuse-bar" style={{ width: `${(c.knowledge / max) * 100}%`, marginTop: 6 }} /></div>
            <span className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>{c.knowledge}</span>
          </div>
        ))}
      </Card>
      <Card>
        <div className="wes-h3" style={{ marginBottom: 6 }}>Who learns together</div>
        <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)", marginBottom: 10 }}>{d.note}</div>
        {d.network.edges.length ? d.network.edges.slice(0, 8).map((e, i) => {
          const a = d.network.nodes.find((n) => n.id === e.from)?.label ?? "Team";
          const b = d.network.nodes.find((n) => n.id === e.to)?.label ?? "Team";
          return <div key={i} className="wes-between" style={{ marginBottom: 8 }}><span style={{ fontSize: "var(--wes-fs-sm)" }}>{a} ↔ {b}</span><Badge tone="info">{e.frequency}×</Badge></div>;
        }) : <Empty title="Collaboration emerging" />}
      </Card>
    </div>
  );
}

/* ---------------- insights ---------------- */
function InsightsView() {
  const [d, setD] = useState<KnowledgeInsights | null>(null);
  useEffect(() => { founderApi.knInsights().then(setD).catch(() => {}); }, []);
  if (!d) return <Card><Skeleton h={150} /></Card>;
  return (
    <div className="wes-grid cols-2 wes-in">
      <Card>
        <Badge tone="ok" dot>Most valuable learning</Badge>
        <p className="wes-h3" style={{ marginTop: 12, fontWeight: 560 }}>{d.most_valuable_learning ?? "—"}</p>
        {d.fastest_growing_domain && <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)", marginTop: 10 }}>Fastest-growing area: <strong style={{ color: "var(--wes-text)" }}>{d.fastest_growing_domain.domain}</strong> (+{d.fastest_growing_domain.new_items})</div>}
      </Card>
      <div className="wes-stack">
        <InsightList title="Emerging opportunities" items={d.emerging_opportunities} />
        <InsightList title="Knowledge at risk (ageing)" items={d.knowledge_at_risk} />
        {d.requires_founder_approval.length > 0 && <InsightList title="Needs your approval" items={d.requires_founder_approval} />}
      </div>
    </div>
  );
}
function InsightList({ title, items }: { title: string; items: string[] }) {
  return (
    <Card>
      <div className="wes-h3" style={{ marginBottom: 12 }}>{title}</div>
      {items.length ? items.map((x, i) => <div key={i} className="wes-search-item">{x}</div>) : <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)" }}>Nothing flagged.</div>}
    </Card>
  );
}

/* ---------------- universal search ---------------- */
function KnSearch() {
  const [q, setQ] = useState(""); const [res, setRes] = useState<BrainSearch | null>(null); const [busy, setBusy] = useState(false);
  const t = useRef<number | undefined>(undefined);
  function run(v: string) {
    setQ(v); window.clearTimeout(t.current);
    if (v.trim().length < 3) { setRes(null); return; }
    t.current = window.setTimeout(async () => { setBusy(true); try { setRes(await founderApi.knSearch(v)); } finally { setBusy(false); } }, 350);
  }
  return (
    <section className="wes-in wes-in-2">
      <div className="wes-search-box"><span className="wes-dim">⌕</span>
        <input placeholder="Search everything the company knows…" value={q} onChange={(e) => run(e.target.value)} />{busy && <Thinking />}</div>
      {res && res.total > 0 && (
        <div className="wes-search-group">
          {g("Knowledge", res.results.knowledge.map((x) => `${x.title} · ${x.similarity}%`))}
          {g("Missions", res.results.missions.map((x) => x.title))}
          {g("Previous projects", res.results.previous_projects.map((x) => x.title))}
          {g("Recommendations", res.results.recommendations.map((x) => x.title))}
        </div>
      )}
      {res && res.total === 0 && <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)", marginTop: 12 }}>Nothing found for "{res.query}".</div>}
    </section>
  );
  function g(label: string, items: string[]) {
    if (!items.length) return null;
    return <div style={{ marginBottom: 14 }}><div className="wes-rail-k" style={{ marginBottom: 8 }}>{label}</div>{items.slice(0, 5).map((x, i) => <div key={i} className="wes-search-item">{x}</div>)}</div>;
  }
}

function Metric({ n, k, s }: { n: string | number; k: string; s: string }) {
  return <div className="wes-kmetric"><div className="n">{n}</div><div className="k">{k}</div><div className="s">{s}</div></div>;
}

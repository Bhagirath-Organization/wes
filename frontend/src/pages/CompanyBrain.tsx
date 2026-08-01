import { useEffect, useMemo, useRef, useState } from "react";

import {
  founderApi, type BrainHome, type BrainLearning, type BrainMemory, type BrainMission, type BrainSearch,
} from "../api/founder";
import { Badge, Card, Empty, ProgressRing, Skeleton, Thinking } from "../components/ui/kit";

const REF_ORDER = ["knowledge", "memory", "learning", "blueprint", "repository", "improvements"];
const REF_LABEL: Record<string, string> = {
  knowledge: "Knowledge", memory: "Memories", learning: "Learnings",
  blueprint: "Blueprint", repository: "Capabilities", improvements: "Improvements",
};

export function CompanyBrain() {
  const [home, setHome] = useState<BrainHome | null>(null);
  const [memory, setMemory] = useState<BrainMemory | null>(null);
  const [learning, setLearning] = useState<BrainLearning | null>(null);
  const [view, setView] = useState<"overview" | "memory" | "learning">("overview");
  const [openId, setOpenId] = useState<string | null>(null);

  useEffect(() => {
    const load = () => founderApi.brainHome().then(setHome).catch(() => {});
    load();
    const iv = setInterval(load, 15000);
    return () => clearInterval(iv);
  }, []);
  useEffect(() => { if (view === "memory" && !memory) founderApi.brainMemory().then(setMemory).catch(() => {}); }, [view, memory]);
  useEffect(() => { if (view === "learning" && !learning) founderApi.brainLearning().then(setLearning).catch(() => {}); }, [view, learning]);

  if (openId) return <MissionIntelligence id={openId} onBack={() => setOpenId(null)} />;

  return (
    <div className="wes-page wes-stack">
      {/* hero */}
      <section className="wes-brain-hero wes-in wes-in-1">
        <div className="wes-row" style={{ gap: 18 }}>
          <div className="wes-brain-orb" />
          <div>
            <div className="wes-eyebrow" style={{ marginBottom: 6 }}>Company Brain</div>
            <h1 className="wes-h1">How your company thinks.</h1>
            <p className="wes-dim" style={{ marginTop: 6 }}>What it knows, why it believes it, and how confident it is — in plain business terms.</p>
          </div>
        </div>
        {home && (
          <div className="wes-row" style={{ marginTop: 22, gap: 20, flexWrap: "wrap" }}>
            <div className="wes-row" style={{ gap: 8 }}><span className="wes-live-dot" /><span className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)" }}>{home.thinking_topics.length} topics under active reasoning · company {home.company_health}</span></div>
            {home.evolution_score != null && <Badge tone="info">Evolution {home.evolution_score}</Badge>}
          </div>
        )}
      </section>

      <BrainSearchBar />

      {!home ? <div className="wes-refs">{REF_ORDER.map((k) => <Card key={k}><Skeleton h={40} /></Card>)}</div> : (
        <>
          {/* references */}
          <section className="wes-refs wes-in wes-in-2">
            {REF_ORDER.map((k) => (
              <div key={k} className="wes-ref"><div className="wes-ref-n">{home.references[k] ?? 0}</div><div className="wes-ref-k">{REF_LABEL[k]}</div></div>
            ))}
          </section>

          <div className="wes-grid cols-2 wes-in wes-in-3">
            {/* thinking stream */}
            <section>
              <div className="wes-h3" style={{ marginBottom: 14 }}>AI Thinking Stream</div>
              <Card>
                <div className="wes-stream">
                  {home.thinking_stream.map((s, i) => (
                    <div key={i} className="wes-stream-row"><span className="wes-live-dot" /><span>{s.event}</span></div>
                  ))}
                </div>
              </Card>
            </section>
            {/* current recommendation */}
            <section>
              <div className="wes-h3" style={{ marginBottom: 14 }}>Current Recommendation</div>
              <Card style={{ height: "calc(100% - 38px)" }}>
                {home.current_recommendation ? (
                  <>
                    <Badge tone="info" dot>The company advises</Badge>
                    <p className="wes-h3" style={{ marginTop: 14, fontWeight: 560 }}>{home.current_recommendation}</p>
                  </>
                ) : <Empty title="No open recommendation" />}
              </Card>
            </section>
          </div>

          {/* thinking topics */}
          <section className="wes-in wes-in-4">
            <div className="wes-h3" style={{ marginBottom: 14 }}>Currently reasoning about</div>
            <div className="wes-mgrid">
              {home.thinking_topics.map((t) => (
                <Card key={t.mission_id} hover className="wes-topic" onClick={() => setOpenId(t.mission_id)} style={{ cursor: "pointer" }}>
                  <div className="wes-between"><Badge tone="info" dot>{t.executive.replace(/^AI /, "")}</Badge><span className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>{t.confidence}%</span></div>
                  <div style={{ fontWeight: 620, lineHeight: 1.3 }}>{clip(t.topic, 70)}</div>
                  <div className="wes-row" style={{ gap: 8 }}><span className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)" }}>{t.activity}</span><Thinking /></div>
                  <div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>Click to see the reasoning →</div>
                </Card>
              ))}
            </div>
          </section>

          {/* sub-views: memory / learning */}
          <section className="wes-in">
            <div className="wes-seg-nav" style={{ marginBottom: 18 }}>
              {(["overview", "memory", "learning"] as const).map((v) => (
                <button key={v} className={`wes-seg-btn${view === v ? " active" : ""}`} onClick={() => setView(v)}>
                  {v === "overview" ? "Overview" : v === "memory" ? "Memory Center" : "Learning Center"}
                </button>
              ))}
            </div>
            {view === "memory" && <MemoryCenter m={memory} />}
            {view === "learning" && <LearningCenter l={learning} />}
            {view === "overview" && <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)" }}>Switch to Memory or Learning to explore what the company remembers and how it improves.</div>}
          </section>
        </>
      )}
    </div>
  );
}

/* -------------------- universal search -------------------- */
function BrainSearchBar() {
  const [q, setQ] = useState("");
  const [res, setRes] = useState<BrainSearch | null>(null);
  const [busy, setBusy] = useState(false);
  const t = useRef<number | undefined>(undefined);
  function run(v: string) {
    setQ(v);
    window.clearTimeout(t.current);
    if (v.trim().length < 3) { setRes(null); return; }
    t.current = window.setTimeout(async () => {
      setBusy(true);
      try { setRes(await founderApi.brainSearch(v)); } finally { setBusy(false); }
    }, 350);
  }
  return (
    <section className="wes-in wes-in-2">
      <div className="wes-search-box">
        <span className="wes-dim">⌕</span>
        <input placeholder="Search everything the company knows…" value={q} onChange={(e) => run(e.target.value)} />
        {busy && <Thinking />}
      </div>
      {res && res.total > 0 && (
        <div className="wes-search-group">
          {group("Missions", res.results.missions.map((x) => x.title))}
          {group("Knowledge", res.results.knowledge.map((x) => `${x.title}  ·  ${x.similarity}% match`))}
          {group("Previous projects", res.results.previous_projects.map((x) => x.title))}
          {group("Recommendations", res.results.recommendations.map((x) => x.title))}
        </div>
      )}
      {res && res.total === 0 && <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)", marginTop: 12 }}>Nothing found for "{res.query}".</div>}
    </section>
  );
  function group(label: string, items: string[]) {
    if (!items.length) return null;
    return (
      <div style={{ marginBottom: 14 }}>
        <div className="wes-rail-k" style={{ marginBottom: 8 }}>{label}</div>
        {items.slice(0, 5).map((x, i) => <div key={i} className="wes-search-item">{x}</div>)}
      </div>
    );
  }
}

/* -------------------- Memory / Learning -------------------- */
function MemoryCenter({ m }: { m: BrainMemory | null }) {
  if (!m) return <Card><Skeleton h={120} /></Card>;
  return (
    <div className="wes-grid cols-2">
      <Card>
        <div className="wes-h3" style={{ marginBottom: 12 }}>What the company remembers</div>
        <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)", marginBottom: 14 }}>{m.total} memories across {m.by_category.length} areas</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {m.by_category.slice(0, 12).map((c) => <span key={c.category} className="wes-chip-sm">{c.category} · {c.count}</span>)}
        </div>
      </Card>
      <Card>
        <div className="wes-h3" style={{ marginBottom: 12 }}>Mistakes it now avoids</div>
        {m.mistakes_avoided.length ? (
          <ul style={{ margin: 0, paddingLeft: 16, color: "var(--wes-text-2)", fontSize: "var(--wes-fs-sm)", lineHeight: 1.6 }}>
            {m.mistakes_avoided.map((x, i) => <li key={i}>{x}</li>)}
          </ul>
        ) : <Empty title="Learning in progress" />}
      </Card>
    </div>
  );
}
function LearningCenter({ l }: { l: BrainLearning | null }) {
  if (!l) return <Card><Skeleton h={120} /></Card>;
  return (
    <div className="wes-grid cols-2">
      <Card>
        <div className="wes-between" style={{ marginBottom: 14 }}>
          <div><div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)" }}>Learning score</div><div className="wes-h1">{l.learning_score ?? "—"}</div></div>
          <ProgressRing value={l.learning_score ?? 0} />
        </div>
        <div className="wes-rail-k">New knowledge gained</div>
        <ul style={{ margin: "8px 0 0", paddingLeft: 16, color: "var(--wes-text-2)", fontSize: "var(--wes-fs-sm)", lineHeight: 1.6 }}>
          {l.new_knowledge.slice(0, 5).map((x, i) => <li key={i}>{x}</li>)}
        </ul>
      </Card>
      <Card>
        <div className="wes-h3" style={{ marginBottom: 12 }}>Emerging opportunities</div>
        {l.emerging_opportunities.length ? l.emerging_opportunities.map((x, i) => (
          <div key={i} className="wes-search-item">{x}</div>
        )) : <Empty title="None yet" />}
      </Card>
    </div>
  );
}

/* -------------------- Mission Intelligence (deep) -------------------- */
function MissionIntelligence({ id, onBack }: { id: string; onBack: () => void }) {
  const [d, setD] = useState<BrainMission | null>(null);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => { founderApi.brainMission(id).then(setD).catch((e) => setErr(e?.message ?? "error")); }, [id]);

  if (err) return <div className="wes-page"><button className="wes-btn wes-btn-quiet wes-btn-sm" onClick={onBack}>← Back</button><Card style={{ marginTop: 16 }}><Empty icon="⚠" title="Couldn't open the reasoning" /></Card></div>;
  if (!d) return <div className="wes-page wes-stack"><Card><Skeleton h={30} w="50%" /></Card><Card><Skeleton h={200} /></Card><Card><Skeleton h={300} /></Card></div>;

  const r = d.reasoning; const ex = d.decision_explainer;
  return (
    <div className="wes-page wes-stack">
      <button className="wes-btn wes-btn-quiet wes-btn-sm" style={{ alignSelf: "flex-start" }} onClick={onBack}>← Company Brain</button>

      <section className="wes-brain-hero wes-in wes-in-1">
        <div className="wes-eyebrow" style={{ marginBottom: 8 }}>Reasoning Explorer</div>
        <h1 className="wes-h1" style={{ lineHeight: 1.25 }}>{d.mission_name}</h1>
        <p className="wes-muted" style={{ marginTop: 12, maxWidth: 640 }}>{r.business_context}</p>
        <div className="wes-row" style={{ marginTop: 16, gap: 14 }}>
          <Badge tone="ok" dot>{Math.round((r.confidence ?? 0) * 100)}% confidence</Badge>
          {r.business_impact && <span className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)" }}>{clip(r.business_impact, 90)}</span>}
        </div>
      </section>

      {/* structured reasoning */}
      <div className="wes-reason-grid wes-in wes-in-2">
        <Block title="Objectives" items={r.objectives} />
        <Block title="What we know" items={r.known_facts} />
        <Block title="Evidence" items={r.evidence} />
        <Block title="Assumptions" items={r.assumptions} />
        <Block title="Open questions" items={r.unknowns} />
        <Block title="Expected risks" items={r.expected_risks} />
      </div>

      {/* alternatives */}
      <Card className="wes-in wes-in-3">
        <div className="wes-h3" style={{ marginBottom: 14 }}>Approaches considered</div>
        {r.alternatives.map((a, i) => (
          <div key={i} className={`wes-alt${a.chosen ? " chosen" : ""}`}>
            <div className="wes-between"><span style={{ fontWeight: 600 }}>{a.option}</span>{a.chosen && <Badge tone="ok">Chosen</Badge>}</div>
            <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)", marginTop: 6 }}>{a.summary}</div>
          </div>
        ))}
        {r.why_alternatives_rejected.length > 0 && (
          <div style={{ marginTop: 12 }}>
            <div className="wes-rail-k">Why the others were set aside</div>
            <ul style={{ margin: "8px 0 0", paddingLeft: 16, color: "var(--wes-text-2)", fontSize: "var(--wes-fs-sm)" }}>
              {r.why_alternatives_rejected.map((x, i) => <li key={i}>{x}</li>)}
            </ul>
          </div>
        )}
        <div style={{ marginTop: 16, borderTop: "1px solid var(--wes-line)", paddingTop: 14 }}>
          <div className="wes-rail-k">Final recommendation</div>
          <div style={{ marginTop: 6, fontWeight: 540 }}>{r.final_recommendation}</div>
        </div>
      </Card>

      {/* decision explainer */}
      <Card className="wes-in">
        <div className="wes-h3" style={{ marginBottom: 14 }}>Why? — the decision, explained</div>
        <div className="wes-reason-grid">
          <ExpBlock k="Why this approach" v={ex.why_this} />
          <ExpBlock k="Why not another" v={ex.why_not_other} />
          <ExpBlock k="Why this confidence" v={ex.why_confidence} />
          <ExpBlock k="What would change it" v={ex.what_would_change_it.join(" · ") || "Stronger counter-evidence."} />
        </div>
      </Card>

      {/* blueprint + domain + repository + memory + graph */}
      <div className="wes-detail-grid">
        <div className="wes-stack">
          <Card>
            <div className="wes-h3" style={{ marginBottom: 14 }}>Knowledge Graph</div>
            <KnowledgeGraph nodes={d.graph.nodes} edges={d.graph.edges} />
          </Card>
          <Card>
            <div className="wes-h3" style={{ marginBottom: 14 }}>Domain Intelligence</div>
            <DomainBlock domain={d.domain} />
          </Card>
        </div>
        <div className="wes-stack">
          <Card>
            <div className="wes-h3" style={{ marginBottom: 14 }}>Blueprint Intelligence</div>
            {d.blueprint.volumes_guiding.map((v, i) => (
              <div key={i} style={{ marginBottom: 12 }}>
                <div style={{ fontWeight: 600, fontSize: "var(--wes-fs-sm)" }}>{v.volume}</div>
                <div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)", marginTop: 2 }}>{v.why}</div>
              </div>
            ))}
            {d.blueprint.compliance_percentage != null && <Badge tone={d.blueprint.compliance_percentage >= 80 ? "ok" : "warn"}>Compliance {d.blueprint.compliance_percentage}%</Badge>}
            {d.blueprint.missing_requirements.length > 0 && (
              <div style={{ marginTop: 12 }}><div className="wes-rail-k">To strengthen</div>
                <ul style={{ margin: "6px 0 0", paddingLeft: 16, color: "var(--wes-text-2)", fontSize: "var(--wes-fs-sm)" }}>{d.blueprint.missing_requirements.map((x, i) => <li key={i}>{x}</li>)}</ul></div>
            )}
          </Card>
          <Card>
            <div className="wes-h3" style={{ marginBottom: 14 }}>Reusable Capabilities</div>
            {d.repository.reusable_capabilities.length ? d.repository.reusable_capabilities.map((c, i) => (
              <div key={i} style={{ marginBottom: 10 }}><div style={{ fontWeight: 560, fontSize: "var(--wes-fs-sm)" }}>{c.capability}</div><div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>{c.why}</div></div>
            )) : <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)" }}>Building fresh for this mission.</div>}
            <div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)", marginTop: 8 }}>{d.repository.business_impact}</div>
          </Card>
          {d.memory.similar_projects.length > 0 && (
            <Card>
              <div className="wes-h3" style={{ marginBottom: 12 }}>Learning from the past</div>
              {d.memory.similar_projects.map((p, i) => (
                <div key={i} className="wes-between" style={{ marginBottom: 8 }}><span style={{ fontSize: "var(--wes-fs-sm)" }}>{clip(p.objective, 50)}</span><Badge tone="info">{p.similarity}%</Badge></div>
              ))}
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

/* radial, dependency-free knowledge graph */
function KnowledgeGraph({ nodes, edges }: { nodes: BrainMission["graph"]["nodes"]; edges: BrainMission["graph"]["edges"] }) {
  const W = 520, H = 420, cx = W / 2, cy = H / 2;
  const colors: Record<string, string> = { mission: "#8b6dff", department: "#6d8bff", executive: "#43d9c7", knowledge: "#f5b544", rule: "#a8b0c4", risk: "#ff6b7d", recommendation: "#37d39b" };
  const pos = useMemo(() => {
    const others = nodes.filter((n) => n.id !== "mission");
    const p: Record<string, { x: number; y: number }> = { mission: { x: cx, y: cy } };
    const R1 = 120, R2 = 185;
    others.forEach((n, i) => {
      const a = (i / others.length) * Math.PI * 2 - Math.PI / 2;
      const r = i % 2 === 0 ? R2 : R1;
      p[n.id] = { x: cx + Math.cos(a) * r, y: cy + Math.sin(a) * r };
    });
    return p;
  }, [nodes]);
  return (
    <svg className="wes-graph" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="xMidYMid meet">
      {edges.map((e, i) => { const a = pos[e.from], b = pos[e.to]; if (!a || !b) return null;
        return <line key={i} className="lnk" x1={a.x} y1={a.y} x2={b.x} y2={b.y} />; })}
      {nodes.map((n) => { const pt = pos[n.id]; if (!pt) return null; const isM = n.group === "mission";
        return (
          <g key={n.id} className="node" transform={`translate(${pt.x},${pt.y})`}>
            <circle r={isM ? 12 : 6} fill={colors[n.group] ?? "#6d8bff"} opacity={isM ? 1 : 0.9} />
            <text x={isM ? 0 : 10} y={isM ? 26 : 3} textAnchor={isM ? "middle" : "start"}>{clip(n.label, 18)}</text>
          </g>
        ); })}
    </svg>
  );
}

function Block({ title, items }: { title: string; items: string[] }) {
  if (!items?.length) return null;
  return <div className="wes-rblock"><h4>{title}</h4><ul>{items.map((x, i) => <li key={i}>{x}</li>)}</ul></div>;
}
function ExpBlock({ k, v }: { k: string; v: string }) {
  return <div className="wes-rblock"><h4>{k}</h4><div style={{ color: "var(--wes-text-2)", fontSize: "var(--wes-fs-sm)", lineHeight: 1.6 }}>{v}</div></div>;
}
function DomainBlock({ domain }: { domain: Record<string, unknown> }) {
  const rows: [string, unknown][] = [
    ["Industry", domain.industry], ["Business model", domain.business_model],
    ["KPIs", domain.kpis], ["Compliance", domain.compliance],
    ["Departments", domain.departments], ["Automation", domain.automation_opportunities],
  ];
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {rows.filter(([, v]) => v && (Array.isArray(v) ? v.length : true)).map(([k, v]) => (
        <div key={k}><div className="wes-rail-k">{k}</div>
          <div style={{ fontSize: "var(--wes-fs-sm)", color: "var(--wes-text-2)", marginTop: 3 }}>{Array.isArray(v) ? (v as string[]).slice(0, 4).join(" · ") : String(v)}</div></div>
      ))}
    </div>
  );
}
function clip(s: string, n: number) { return (s ?? "").length > n ? s.slice(0, n - 1) + "…" : (s ?? ""); }

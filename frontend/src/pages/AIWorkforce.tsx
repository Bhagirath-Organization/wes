import { useEffect, useMemo, useState } from "react";

import {
  founderApi, type CollabNetwork, type EmployeeProfile, type HiringPipeline,
  type OrgChart, type WorkforceHome, type WorkforceMember,
} from "../api/founder";
import { Badge, Card, Empty, Skeleton, Thinking } from "../components/ui/kit";

const initials = (s: string) => (s || "AI").split(" ").map((w) => w[0]).slice(0, 2).join("").toUpperCase();

export function AIWorkforce() {
  const [home, setHome] = useState<WorkforceHome | null>(null);
  const [tab, setTab] = useState<"team" | "org" | "collab" | "hiring">("team");
  const [openId, setOpenId] = useState<string | null>(null);
  const [q, setQ] = useState("");

  useEffect(() => {
    const load = () => founderApi.workforceHome().then(setHome).catch(() => {});
    load();
    const iv = setInterval(load, 20000);
    return () => clearInterval(iv);
  }, []);

  if (openId) return <Profile id={openId} onBack={() => setOpenId(null)} />;

  const filtered = (m: WorkforceMember) => !q || `${m.name} ${m.role} ${m.department}`.toLowerCase().includes(q.toLowerCase());

  return (
    <div className="wes-page wes-stack">
      <div className="wes-between wes-in wes-in-1" style={{ flexWrap: "wrap", gap: 16 }}>
        <div>
          <div className="wes-eyebrow" style={{ marginBottom: 8 }}>AI Workforce</div>
          <h1 className="wes-h1">Your AI organisation.</h1>
          <p className="wes-dim" style={{ marginTop: 6 }}>An executive team and an engineering org — see who's working, and how they perform.</p>
        </div>
        {home && (
          <div className="wes-row"><span className="wes-live-dot" /><span className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)" }}>{home.summary.working} engaged · {home.summary.available} available</span></div>
        )}
      </div>

      {home && (
        <section className="wes-wf-summary wes-in wes-in-2">
          <Stat k="Team" v={home.summary.total} s="AI employees" />
          <Stat k="Engaged" v={home.summary.working} s="working now" />
          <Stat k="Available" v={home.summary.available} s="ready for work" />
          <Stat k="Departments" v={home.summary.departments} s="organised teams" />
        </section>
      )}

      <div className="wes-between wes-in wes-in-3" style={{ flexWrap: "wrap", gap: 12 }}>
        <div className="wes-seg-nav">
          {([["team", "Team"], ["org", "Org Chart"], ["collab", "Collaboration"], ["hiring", "Future Workforce"]] as const).map(([v, l]) => (
            <button key={v} className={`wes-seg-btn${tab === v ? " active" : ""}`} onClick={() => setTab(v)}>{l}</button>
          ))}
        </div>
        {tab === "team" && (
          <div className="wes-search-box" style={{ maxWidth: 300, padding: "2px 6px 2px 14px" }}>
            <span className="wes-dim">⌕</span>
            <input placeholder="Search the workforce…" value={q} onChange={(e) => setQ(e.target.value)} style={{ padding: "9px 0" }} />
          </div>
        )}
      </div>

      {!home ? <div className="wes-people">{[0, 1, 2, 3].map((i) => <Card key={i}><Skeleton h={80} /></Card>)}</div> : (
        <>
          {tab === "team" && home.teams.map((t) => {
            const members = t.members.filter(filtered);
            if (!members.length) return null;
            return (
              <section key={t.department} className="wes-team wes-in">
                <div className="wes-team-head"><span className="wes-team-name">{t.department}</span><span className="wes-team-count">{members.length} members</span></div>
                <div className="wes-people">
                  {members.map((m) => (
                    <div key={m.id} className={`wes-person${m.status === "working" ? " working" : ""}`} role="button" tabIndex={0}
                      onClick={() => setOpenId(m.id)} onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); setOpenId(m.id); } }}>
                      <div className="wes-person-top">
                        <div className="wes-person-av">{initials(m.name)}</div>
                        <div style={{ minWidth: 0 }}>
                          <div className="wes-person-name">{m.name}</div>
                          <div className="wes-person-role">{m.role}</div>
                        </div>
                        <span className={`wes-live-dot${m.status !== "working" ? " ready" : ""}`} style={{ marginLeft: "auto" }} />
                      </div>
                      <div className="wes-person-work">{m.status === "working" ? m.current_work : m.availability}</div>
                      <div className="wes-person-foot">
                        <span>{m.status === "working" ? `${m.confidence}% confident` : "Available"}</span>
                        <span>{m.knowledge > 0 ? `${m.knowledge} learned` : ""}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            );
          })}

          {tab === "org" && <OrgChartView onOpen={setOpenId} />}
          {tab === "collab" && <CollaborationView />}
          {tab === "hiring" && <HiringView />}
        </>
      )}
    </div>
  );
}

/* -------------------- profile -------------------- */
function Profile({ id, onBack }: { id: string; onBack: () => void }) {
  const [d, setD] = useState<EmployeeProfile | null>(null);
  const [err, setErr] = useState(false);
  useEffect(() => { founderApi.employee(id).then(setD).catch(() => setErr(true)); }, [id]);
  if (err) return <div className="wes-page"><button className="wes-btn wes-btn-quiet wes-btn-sm" onClick={onBack}>← Back</button><Card style={{ marginTop: 16 }}><Empty title="Profile unavailable" /></Card></div>;
  if (!d) return <div className="wes-page wes-stack"><Card><Skeleton h={90} /></Card><Card><Skeleton h={220} /></Card></div>;
  const p = d.performance;
  return (
    <div className="wes-page wes-stack">
      <button className="wes-btn wes-btn-quiet wes-btn-sm" style={{ alignSelf: "flex-start" }} onClick={onBack}>← AI Workforce</button>
      <section className="wes-hero wes-in wes-in-1">
        <div className="wes-row" style={{ gap: 18, flexWrap: "wrap" }}>
          <div className="wes-person-av" style={{ width: 64, height: 64, borderRadius: 20, background: d.status === "working" ? "var(--wes-accent-grad)" : "var(--wes-bg-4)", color: d.status === "working" ? "#0b0d14" : "var(--wes-text-2)", fontSize: "1.1rem" }}>{initials(d.name)}</div>
          <div style={{ flex: 1, minWidth: 240 }}>
            <h1 className="wes-h1">{d.name}</h1>
            <p className="wes-muted" style={{ marginTop: 4 }}>{d.role} · {d.department} · reports to {d.reports_to}</p>
            <div className="wes-row" style={{ marginTop: 12, gap: 10 }}>
              <Badge tone={d.status === "working" ? "info" : "neutral"} dot>{d.availability}</Badge>
              {d.current_mission && <span className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)" }}>{d.current_work}</span>}
              {d.status === "working" && <Thinking />}
            </div>
          </div>
        </div>
      </section>

      <div className="wes-profile-grid">
        <div className="wes-stack">
          <Card>
            <div className="wes-h3" style={{ marginBottom: 14 }}>Performance</div>
            <div className="wes-perf">
              <div><div className="n">{p.completed}</div><div className="k">Completed</div></div>
              <div><div className="n">{p.approval_rate != null ? `${p.approval_rate}%` : "—"}</div><div className="k">Approval rate</div></div>
              <div><div className="n">{p.knowledge_items}</div><div className="k">Knowledge</div></div>
            </div>
            <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)", marginTop: 14 }}>Quality: <strong style={{ color: "var(--wes-text)" }}>{p.quality}</strong> · {p.contributions} contributions</div>
          </Card>
          <Card>
            <div className="wes-h3" style={{ marginBottom: 12 }}>Recent work</div>
            {d.mission_history.length ? (
              <div className="wes-timeline">
                {d.mission_history.slice(0, 6).map((m, i) => <div key={i} className="wes-tl-item done"><div style={{ fontWeight: 540, fontSize: "var(--wes-fs-sm)" }}>{m}</div></div>)}
              </div>
            ) : <Empty title="No missions yet" />}
            <div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)", marginTop: 10 }}>Last activity: {d.last_activity}</div>
          </Card>
        </div>

        <div className="wes-stack">
          <Card>
            <div className="wes-h3" style={{ marginBottom: 12 }}>Skills</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 12 }}>
              <span className="wes-skill" style={{ borderColor: "rgba(109,139,255,.35)" }}>{d.skills.primary}</span>
              {d.skills.secondary.map((s, i) => <span key={i} className="wes-skill">{s}</span>)}
            </div>
            {d.knowledge_areas.length > 0 && <>
              <div className="wes-rail-k">Knowledge areas</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 8 }}>{d.knowledge_areas.map((k, i) => <span key={i} className="wes-chip-sm">{k}</span>)}</div>
            </>}
          </Card>
          <Card>
            <div className="wes-h3" style={{ marginBottom: 12 }}>Responsibilities</div>
            <ul style={{ margin: 0, paddingLeft: 16, color: "var(--wes-text-2)", fontSize: "var(--wes-fs-sm)", lineHeight: 1.6 }}>
              {d.responsibilities.map((r, i) => <li key={i}>{r}</li>)}
            </ul>
          </Card>
          {d.collaboration.length > 0 && (
            <Card>
              <div className="wes-h3" style={{ marginBottom: 12 }}>Works closely with</div>
              {d.collaboration.map((c, i) => <div key={i} className="wes-between" style={{ marginBottom: 8 }}><span style={{ fontSize: "var(--wes-fs-sm)" }}>{c.with}</span><Badge tone="info">{c.frequency}×</Badge></div>)}
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

/* -------------------- org chart -------------------- */
function OrgChartView({ onOpen }: { onOpen: (id: string) => void }) {
  const [d, setD] = useState<OrgChart | null>(null);
  useEffect(() => { founderApi.orgChart().then(setD).catch(() => {}); }, []);
  if (!d) return <Card><Skeleton h={200} /></Card>;
  const cols = [
    { k: "Leadership", nodes: d.nodes.filter((n) => n.group === "founder" || n.group === "ceo") },
    { k: "Departments", nodes: d.nodes.filter((n) => n.group === "department") },
    { k: "AI Employees", nodes: d.nodes.filter((n) => n.group === "employee") },
  ];
  return (
    <Card className="wes-in">
      <div className="wes-h3" style={{ marginBottom: 16 }}>Organisation Chart</div>
      <div className="wes-orgcols">
        {cols.map((c) => (
          <div key={c.k} className="wes-orgcol">
            <div className="wes-orgcol-k">{c.k}</div>
            {c.nodes.map((n) => (
              <div key={n.id} className={`wes-orgnode ${n.group}`} role={n.group === "employee" || n.group === "ceo" ? "button" : undefined}
                tabIndex={n.group === "employee" || n.group === "ceo" ? 0 : undefined}
                onClick={() => { if (n.group === "employee" || n.group === "ceo") onOpen(n.id); }}
                onKeyDown={(e) => { if ((n.group === "employee" || n.group === "ceo") && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); onOpen(n.id); } }}>
                <div className="nm">{n.label}</div><div className="sb">{n.sub}</div>
              </div>
            ))}
          </div>
        ))}
      </div>
    </Card>
  );
}

/* -------------------- collaboration network -------------------- */
function CollaborationView() {
  const [d, setD] = useState<CollabNetwork | null>(null);
  useEffect(() => { founderApi.collaboration().then(setD).catch(() => {}); }, []);
  const pos = useMemo(() => {
    const p: Record<string, { x: number; y: number }> = {};
    const n = d?.nodes ?? [];
    n.forEach((node, i) => { const a = (i / Math.max(n.length, 1)) * Math.PI * 2 - Math.PI / 2; p[node.id] = { x: 260 + Math.cos(a) * 150, y: 210 + Math.sin(a) * 150 }; });
    return p;
  }, [d]);
  if (!d) return <Card><Skeleton h={200} /></Card>;
  return (
    <Card className="wes-in">
      <div className="wes-h3" style={{ marginBottom: 6 }}>Collaboration Network</div>
      <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)", marginBottom: 12 }}>{d.note}</div>
      {d.nodes.length ? (
        <svg className="wes-graph" viewBox="0 0 520 420" preserveAspectRatio="xMidYMid meet">
          {d.edges.map((e, i) => { const a = pos[e.from], b = pos[e.to]; if (!a || !b) return null;
            return <line key={i} x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke="var(--wes-brand)" strokeOpacity={0.15 + e.strength * 0.5} strokeWidth={1 + e.strength * 3} />; })}
          {d.nodes.map((n) => { const pt = pos[n.id]; if (!pt) return null;
            return <g key={n.id} transform={`translate(${pt.x},${pt.y})`}><circle r={9} fill="var(--wes-brand)" /><text x={12} y={4} style={{ fontSize: 11, fill: "var(--wes-text-2)" }}>{n.label}</text></g>; })}
        </svg>
      ) : <Empty title="Collaboration begins with the first mission" />}
    </Card>
  );
}

/* -------------------- hiring pipeline -------------------- */
function HiringView() {
  const [d, setD] = useState<HiringPipeline | null>(null);
  useEffect(() => { founderApi.hiring().then(setD).catch(() => {}); }, []);
  if (!d) return <Card><Skeleton h={150} /></Card>;
  return (
    <section className="wes-in">
      <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)", marginBottom: 16 }}>{d.note}</div>
      <div className="wes-grid cols-3">
        {d.future_roles.map((r) => (
          <Card key={r.role}>
            <div className="wes-between" style={{ marginBottom: 10 }}><span style={{ fontWeight: 640 }}>{r.role}</span><Badge tone={r.status === "Recommended" ? "info" : "ok"}>{r.status}</Badge></div>
            <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)", marginBottom: 10 }}>{r.reason}</div>
            <div className="wes-rail-k">Business value</div>
            <div style={{ fontSize: "var(--wes-fs-sm)", color: "var(--wes-text-2)", marginTop: 3 }}>{r.business_value}</div>
            <div style={{ marginTop: 10 }}><Badge tone="neutral">Impact: {r.expected_impact}</Badge></div>
          </Card>
        ))}
      </div>
    </section>
  );
}

function Stat({ k, v, s }: { k: string; v: number; s: string }) {
  return (
    <Card>
      <div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)", textTransform: "uppercase", letterSpacing: ".1em" }}>{k}</div>
      <div className="wes-h1" style={{ margin: "6px 0 2px" }}>{v}</div>
      <div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>{s}</div>
    </Card>
  );
}

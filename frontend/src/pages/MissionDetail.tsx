import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { founderApi, type MissionDetail as Detail } from "../api/founder";
import { Badge, Card, Empty, ProgressRing, Skeleton, Thinking, stageTone, type Tone } from "../components/ui/kit";

const initials = (s: string) => (s || "AI").replace(/^AI /, "").split(" ").map((w) => w[0]).slice(0, 2).join("").toUpperCase();
const MAP_INITIALS: Record<string, string> = {
  CEO: "CE", CTO: "CT", "Chief Architect": "CA", Engineering: "EN", QA: "QA", Security: "SO", DevOps: "DO", Founder: "YOU",
};
function riskTone(v: string): Tone { const s = v.toLowerCase(); return s === "high" ? "risk" : s === "medium" ? "warn" : "ok"; }

export function MissionDetail() {
  const { id = "" } = useParams();
  const [d, setD] = useState<Detail | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    const load = () => founderApi.missionDetail(id).then((x) => alive && setD(x)).catch((e) => alive && setErr(e?.message ?? "error")).finally(() => alive && setLoading(false));
    load();
    // Mission detail is a heavy composite; refresh gently (the live pulse conveys
    // "alive" without hammering the backend). Live status stays on lighter screens.
    const iv = setInterval(load, 45000);
    return () => { alive = false; clearInterval(iv); };
  }, [id]);

  if (loading && !d) return <div className="wes-page wes-stack"><Card><Skeleton h={120} /></Card><Card><Skeleton h={200} /></Card></div>;
  if (err || !d) return <div className="wes-page"><Card><Empty icon="⚠" title="Couldn't open this mission" hint={err ?? undefined} /></Card></div>;

  const o = d.overview;
  return (
    <div className="wes-page wes-stack">
      <Link to="/missions" className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)", textDecoration: "none" }}>← Mission Center</Link>

      {/* ---------- Overview hero ---------- */}
      <section className="wes-hero wes-in wes-in-1">
        <div className="wes-between" style={{ alignItems: "flex-start", gap: 24, flexWrap: "wrap" }}>
          <div style={{ minWidth: 280, flex: 1 }}>
            <div className="wes-row" style={{ marginBottom: 12, flexWrap: "wrap" }}>
              <Badge tone={stageTone(o.business_stage)} dot>{o.business_stage}</Badge>
              {o.explanation?.founder_action_required && <Badge tone="warn">Your approval needed</Badge>}
              <span className="wes-row" style={{ gap: 6 }}><span className="wes-live-dot" /><span className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>live</span></span>
            </div>
            <h1 className="wes-h1" style={{ lineHeight: 1.25 }}>{o.mission_name}</h1>
            <p className="wes-muted" style={{ marginTop: 10, maxWidth: 620 }}>{o.business_value ?? o.business_goal}</p>
            <div className="wes-row" style={{ marginTop: 16, gap: 8 }}>
              <span className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)" }}>{o.current_executive.replace(/^AI /, "")} · {o.current_activity}</span><Thinking />
            </div>
          </div>
          <ProgressRing value={o.progress} />
        </div>
        {o.explanation && (
          <div className="wes-grid cols-3" style={{ marginTop: 24 }}>
            <Info k="What's happening" v={o.explanation.what_happened} />
            <Info k="Why" v={o.explanation.why} />
            <Info k="What's next" v={o.explanation.what_happens_next} />
          </div>
        )}
      </section>

      {/* ---------- Mission Map ---------- */}
      <Card className="wes-in wes-in-2">
        <div className="wes-h3" style={{ marginBottom: 16 }}>Mission Map</div>
        <div className="wes-map">
          {d.map.roles.map((r, i) => (
            <MapNode key={r} role={r} state={i < d.map.position ? "done" : i === d.map.position ? "current" : "upcoming"} last={i === d.map.roles.length - 1} doneLink={i < d.map.position} />
          ))}
        </div>
        <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)", marginTop: 12 }}>
          The company is with the <strong style={{ color: "var(--wes-brand-ink)" }}>{d.map.current}</strong> right now.
        </div>
      </Card>

      <div className="wes-detail-grid">
        {/* ---------- LEFT: discussions + timeline ---------- */}
        <div className="wes-stack">
          <Card className="wes-in wes-in-3">
            <div className="wes-h3" style={{ marginBottom: 18 }}>Executive Discussion</div>
            {d.discussions.length ? (
              <div className="wes-disc">
                {d.discussions.map((x, i) => (
                  <div key={i} className="wes-disc-row">
                    <div className="wes-disc-av">{initials(x.executive)}</div>
                    <div style={{ minWidth: 0 }}>
                      <div><span className="wes-disc-who">{x.executive}</span><span className="wes-disc-kind">{prettyKind(x.kind)}</span></div>
                      <div className="wes-disc-msg">{x.message}</div>
                    </div>
                  </div>
                ))}
              </div>
            ) : <Empty title="Discussion begins soon" hint="The executives are gathering." />}
          </Card>

          <Card>
            <div className="wes-h3" style={{ marginBottom: 18 }}>Mission Timeline</div>
            {d.timeline.length ? (
              <div className="wes-timeline">
                {d.timeline.slice().reverse().map((e, i) => (
                  <div key={i} className={`wes-tl-item${e.outcome === "done" ? " done" : ""}`}>
                    <div style={{ fontWeight: 560 }}>{e.activity}</div>
                    <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)" }}>{narrate(e.outcome)} · {e.by}</div>
                  </div>
                ))}
              </div>
            ) : <Empty title="The story starts here" />}
          </Card>
        </div>

        {/* ---------- RIGHT: brain + risks + decisions ---------- */}
        <div className="wes-stack">
          <Card className="wes-in wes-in-3">
            <div className="wes-h3" style={{ marginBottom: 14 }}>Company Brain</div>
            <BrainBlock label="What we know" items={d.brain.knows} />
            <BrainBlock label="Assumptions" items={d.brain.assumptions} />
            <BrainBlock label="Guided by" items={d.brain.blueprint_guidance} />
            {d.brain.previous_projects.length > 0 && <BrainBlock label="Learning from" items={d.brain.previous_projects} />}
          </Card>

          <Card>
            <div className="wes-h3" style={{ marginBottom: 6 }}>Risk Center</div>
            {d.risks.length ? d.risks.map((r, i) => (
              <div key={i} className="wes-risk-row">
                <div>
                  <div style={{ fontWeight: 540, fontSize: "var(--wes-fs-sm)" }}>{r.risk}</div>
                  <div className="wes-risk-meta">
                    <span className="wes-chip-sm">{r.category}</span>
                    <span className="wes-chip-sm">Owner: {r.owner}</span>
                  </div>
                  <div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)", marginTop: 6 }}>Mitigation: {r.mitigation}</div>
                </div>
                <div style={{ textAlign: "right", display: "flex", flexDirection: "column", gap: 6, alignItems: "flex-end" }}>
                  <Badge tone={riskTone(r.impact)}>{r.impact} impact</Badge>
                  <span className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>{r.probability} likelihood</span>
                </div>
              </div>
            )) : <Empty title="No open risks" />}
          </Card>

          <Card>
            <div className="wes-h3" style={{ marginBottom: 14 }}>Decision Center</div>
            {d.decisions.pending_founder && (
              <div style={{ marginBottom: 14 }}>
                <Badge tone="warn">Your decision</Badge>
                <div style={{ fontWeight: 560, marginTop: 8 }}>{d.decisions.pending_founder.decision}</div>
              </div>
            )}
            {d.decisions.pending_executive?.decision && (
              <Info k="Executive position" v={`${prettyKind(d.decisions.pending_executive.decision)} — ${d.decisions.pending_executive.rationale}`} />
            )}
            {d.decisions.recommended && <div style={{ marginTop: 12 }}><Info k="Recommended" v={d.decisions.recommended} /></div>}
            {d.decisions.alternatives.length > 0 && (
              <div style={{ marginTop: 12 }}>
                <div className="wes-rail-k">Alternatives considered</div>
                <ul style={{ margin: "8px 0 0", paddingLeft: 18, color: "var(--wes-text-2)", fontSize: "var(--wes-fs-sm)" }}>
                  {d.decisions.alternatives.map((a, i) => <li key={i} style={{ marginBottom: 4 }}>{a}</li>)}
                </ul>
              </div>
            )}
            {!d.decisions.pending_founder && !d.decisions.pending_executive?.decision && <Empty title="No decisions pending" />}
          </Card>
        </div>
      </div>
    </div>
  );
}

function MapNode({ role, state, last, doneLink }: { role: string; state: string; last: boolean; doneLink: boolean }) {
  return (
    <>
      <div className={`wes-map-node ${state}`}>
        <div className="wes-map-orb">{MAP_INITIALS[role] ?? role.slice(0, 2)}</div>
        <div className="wes-map-label">{role}</div>
      </div>
      {!last && <div className={`wes-map-link${doneLink ? " done" : ""}`} />}
    </>
  );
}
function BrainBlock({ label, items }: { label: string; items: string[] }) {
  if (!items.length) return null;
  return (
    <div style={{ marginBottom: 16 }}>
      <div className="wes-rail-k">{label}</div>
      <div style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: 7 }}>
        {items.map((x, i) => <div key={i} className="wes-detail-row" style={{ fontSize: "var(--wes-fs-sm)" }}>✦&nbsp;<span>{x}</span></div>)}
      </div>
    </div>
  );
}
function Info({ k, v }: { k: string; v: string }) {
  return <div><div className="wes-rail-k">{k}</div><div style={{ marginTop: 4, fontSize: "var(--wes-fs-sm)", color: "var(--wes-text-2)", lineHeight: 1.5 }}>{v}</div></div>;
}
function prettyKind(k: string) {
  return ({ changes_requested: "requested changes", approved: "approved", rejected: "raised objections",
    question: "asked", answer: "responded", concern: "raised a concern", decision: "decided",
    endorse: "endorsed", challenge: "challenged", escalation: "escalated" } as Record<string, string>)[k] ?? k.replace(/_/g, " ");
}
function narrate(o: string) { return ({ done: "Completed", "needed rework": "Sent back for improvement", "in progress": "Underway" } as Record<string, string>)[o] ?? o; }

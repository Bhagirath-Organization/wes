import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  founderApi, type LiveCompany, type MissionAnalytics, type MissionsResponse,
} from "../api/founder";
import { Badge, Card, Empty, Skeleton, Thinking, stageTone } from "../components/ui/kit";

/* Business lifecycle → the 11 visible business stages (mirrors the backend). */
const STAGES = ["Understand Business", "Executive Strategy", "Architecture", "Planning",
  "Engineering", "Quality", "Executive Review", "Founder Approval", "Deployment",
  "Business Validation", "Learning"];
const LIFECYCLE_TO_STAGE: Record<string, string> = {
  "Business Objective": "Understand Business", "Business Understanding": "Understand Business",
  "Executive Discussion": "Executive Strategy", "Architecture": "Architecture",
  "Planning": "Planning", "Engineering": "Engineering", "Testing": "Quality",
  "Review": "Executive Review", "Deployment": "Deployment",
  "Business Validation": "Business Validation", "Completed": "Learning",
};
const initials = (s: string) => s.replace(/^AI /, "").split(" ").map((w) => w[0]).slice(0, 2).join("").toUpperCase();

export function MissionCenter() {
  const navigate = useNavigate();
  const [missions, setMissions] = useState<MissionsResponse | null>(null);
  const [live, setLive] = useState<LiveCompany | null>(null);
  const [analytics, setAnalytics] = useState<MissionAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"active" | "all">("active");
  const tick = useRef(0);

  async function refresh() {
    const [m, l, a] = await Promise.all([
      founderApi.missions().catch(() => null),
      founderApi.live().catch(() => null),
      founderApi.missionAnalytics().catch(() => null),
    ]);
    if (m) setMissions(m); if (l) setLive(l); if (a) setAnalytics(a);
    setLoading(false);
  }
  useEffect(() => {
    refresh();
    const iv = setInterval(() => { tick.current++; refresh(); }, 15000); // live: never frozen
    return () => clearInterval(iv);
  }, []);

  // Join live executives to missions by objective so each card shows who's working.
  const liveByObjective = useMemo(() => {
    const map = new Map<string, LiveCompany["executives"][number]>();
    live?.executives.forEach((e) => { if (e.objective) map.set(e.objective, e); });
    return map;
  }, [live]);

  const list = (missions?.missions ?? []).filter((m) => tab === "all" || m.status !== "Completed");

  return (
    <div className="wes-page wes-stack">
      <div className="wes-between wes-in wes-in-1">
        <div>
          <div className="wes-eyebrow" style={{ marginBottom: 8 }}>Mission Center</div>
          <h1 className="wes-h1">Your company, working.</h1>
          <p className="wes-dim" style={{ marginTop: 6 }}>Every mission is a living business initiative — see what's happening, right now.</p>
        </div>
        {live && (
          <div className="wes-row"><span className="wes-live-dot" />
            <span className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)" }}>{live.active_missions} active · company {live.company_health}</span></div>
        )}
      </div>

      {/* ---------- Living Company ---------- */}
      <section className="wes-in wes-in-2">
        <div className="wes-between" style={{ marginBottom: 14 }}>
          <div className="wes-h3">Live Company</div>
          <span className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>updates automatically</span>
        </div>
        {loading && !live ? <div className="wes-livegrid">{[0,1,2,3].map((i)=><Card key={i}><Skeleton h={60}/></Card>)}</div> : (
          <div className="wes-livegrid">
            {live?.executives.filter((e) => e.status === "working").slice(0, 6).map((e, i) => (
              <div key={i} className="wes-livecard working">
                <div className="wes-between">
                  <div className="wes-row">
                    <div className="wes-disc-av" style={{ background: "var(--wes-accent-grad)", color: "#0b0d14" }}>{initials(e.executive)}</div>
                    <div><div style={{ fontWeight: 620, fontSize: "var(--wes-fs-sm)" }}>{e.executive.replace(/^AI /, "")}</div>
                      <div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>{e.stage ?? "Working"}</div></div>
                  </div>
                  <span className="wes-live-dot" />
                </div>
                <div className="wes-row" style={{ gap: 8 }}>
                  <span className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)" }}>{e.thinking}</span><Thinking />
                </div>
                {e.confidence != null && <div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>{e.confidence}% confident · {e.eta}</div>}
              </div>
            ))}
            {live?.executives.filter((e) => e.status === "ready").slice(0, 3).map((e, i) => (
              <div key={`r${i}`} className="wes-livecard">
                <div className="wes-row"><div className="wes-disc-av">{initials(e.executive)}</div>
                  <div><div style={{ fontWeight: 600, fontSize: "var(--wes-fs-sm)" }}>{e.executive.replace(/^AI /, "")}</div>
                    <div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>Standing by</div></div>
                  <span className="wes-live-dot ready" style={{ marginLeft: "auto" }} /></div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* ---------- Analytics ---------- */}
      {analytics && (
        <section className="wes-grid cols-4 wes-in wes-in-3">
          <Stat label="Missions active" value={String(analytics.throughput.active)} sub={`${analytics.throughput.delivered} delivered`} />
          <Stat label="Avg confidence" value={analytics.mission_confidence != null ? `${analytics.mission_confidence}%` : "—"} sub="across all missions" />
          <Stat label="Decisions waiting" value={String(analytics.decision_bottleneck)} sub="need your approval" tone={analytics.decision_bottleneck ? "warn" : "ok"} />
          <Stat label="Value delivered" value={String(analytics.business_value_delivered)} sub="missions shipped" />
        </section>
      )}

      {/* ---------- Missions ---------- */}
      <section className="wes-in wes-in-4">
        <div className="wes-between" style={{ marginBottom: 16 }}>
          <div className="wes-h3">Missions</div>
          <div className="wes-row" style={{ gap: 6 }}>
            <button className={`wes-chip${tab === "active" ? "" : ""}`} style={tab === "active" ? { background: "var(--wes-bg-4)", color: "var(--wes-text)" } : {}} onClick={() => setTab("active")}>Active</button>
            <button className="wes-chip" style={tab === "all" ? { background: "var(--wes-bg-4)", color: "var(--wes-text)" } : {}} onClick={() => setTab("all")}>All</button>
          </div>
        </div>
        {loading && !missions ? (
          <div className="wes-mgrid">{[0,1,2].map((i)=><Card key={i}><Skeleton h={140}/></Card>)}</div>
        ) : list.length ? (
          <div className="wes-mgrid">
            {list.map((m) => {
              const e = liveByObjective.get(m.business_objective ?? "") ?? liveByObjective.get(m.mission_name);
              const stage = LIFECYCLE_TO_STAGE[m.current_stage] ?? "Understand Business";
              const idx = STAGES.indexOf(stage);
              return (
                <Card key={m.mission_id} hover className="wes-mcard" style={{ cursor: "pointer" }}>
                  <div onClick={() => navigate(`/missions/${m.mission_id}`)} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                    <div className="wes-between" style={{ alignItems: "flex-start" }}>
                      <Badge tone={stageTone(stage)} dot>{stage}</Badge>
                      {m.status === "Completed" ? <Badge tone="ok">Delivered</Badge>
                        : stage === "Executive Review" || stage === "Founder Approval" ? <Badge tone="warn">Decision pending</Badge> : null}
                    </div>
                    <div>
                      <div style={{ fontWeight: 640, letterSpacing: "-0.01em", lineHeight: 1.3 }}>{clip(m.mission_name, 84)}</div>
                    </div>
                    <div className="stage-rail">
                      {STAGES.map((_, i) => <span key={i} className={`wes-seg ${i < idx ? "done" : i === idx ? "current" : ""}`} />)}
                    </div>
                    <div className="wes-mmeta">
                      <div><div className="k">Led by</div><div className="v">{(e?.executive ?? "AI CEO").replace(/^AI /, "")}</div></div>
                      <div><div className="k">Confidence</div><div className="v">{m.business_confidence != null ? `${Math.round(m.business_confidence * 100)}%` : "—"}</div></div>
                    </div>
                    {e?.thinking && (
                      <div className="wes-row" style={{ gap: 8, borderTop: "1px solid var(--wes-line-soft)", paddingTop: 12 }}>
                        <span className="wes-live-dot" /><span className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)" }}>{e.thinking}</span>
                      </div>
                    )}
                  </div>
                </Card>
              );
            })}
          </div>
        ) : <Card><Empty title="No missions yet" hint="Start one from Home and it becomes a living initiative here." /></Card>}
      </section>
    </div>
  );
}

function Stat({ label, value, sub, tone }: { label: string; value: string; sub: string; tone?: "ok" | "warn" }) {
  return (
    <Card>
      <div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)", textTransform: "uppercase", letterSpacing: ".1em" }}>{label}</div>
      <div className="wes-h1" style={{ margin: "6px 0 2px", color: tone === "warn" ? "var(--wes-warn)" : undefined }}>{value}</div>
      <div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>{sub}</div>
    </Card>
  );
}
function clip(s: string, n: number) { return s.length > n ? s.slice(0, n - 1) + "…" : s; }

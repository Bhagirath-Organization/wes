import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAsync } from "../hooks/useAsync";
import { useSession } from "../auth/SessionContext";
import { workApi } from "../api/work";
import {
  founderApi, type CompanyHealth, type EvolutionView, type FounderDecision,
  type MissionDashboard, type MissionsResponse,
} from "../api/founder";
import {
  Badge, Button, Card, Empty, ProgressBar, ProgressRing, Skeleton, Thinking,
  healthTone, stageTone, type Tone,
} from "../components/ui/kit";

/* ---------------------------------------------------------------------- */
/*  Founder Home — the first screen. Understand the company in 5 seconds. */
/* ---------------------------------------------------------------------- */

interface HomeData {
  missions: MissionsResponse;
  health: CompanyHealth;
  decisions: FounderDecision[];
  evolution: EvolutionView;
  current?: MissionDashboard;
  currentId?: string;
  activity: { activity: string; outcome: string }[];
}

async function loadHome(): Promise<HomeData> {
  const [missions, health, decisionsRes, evolution] = await Promise.all([
    founderApi.missions(),
    founderApi.companyHealth(),
    founderApi.decisions(),
    founderApi.evolution(),
  ]);
  const active = missions.missions.find((m) => m.status !== "Completed") ?? missions.missions[0];
  let current: MissionDashboard | undefined;
  let activity: { activity: string; outcome: string }[] = [];
  if (active) {
    const [c, t] = await Promise.all([
      founderApi.mission(active.mission_id).catch(() => undefined),
      founderApi.timeline(active.mission_id).catch(() => ({ events: [], total_activities: 0 })),
    ]);
    current = c;
    activity = (t.events || []).slice(-6).reverse();
  }
  return { missions, health, decisions: decisionsRes.items, evolution, current, currentId: active?.mission_id, activity };
}

function greeting() {
  const h = new Date().getHours();
  return h < 12 ? "Good morning" : h < 18 ? "Good afternoon" : "Good evening";
}

const EXECUTIVES = [
  { key: "AI CEO", role: "CEO", focus: "Business & vision" },
  { key: "AI CTO", role: "CTO", focus: "Technology strategy" },
  { key: "AI Chief Architect", role: "Chief Architect", focus: "Architecture & reuse" },
  { key: "AI Engineering Team", role: "Engineering", focus: "Building the product" },
  { key: "AI QA Lead", role: "Quality", focus: "Verification & standards" },
  { key: "AI Security Engineer", role: "Security", focus: "Risk & compliance" },
];

export function FounderHome() {
  const { user } = useSession();
  const navigate = useNavigate();
  const { data, loading, error, reload } = useAsync<HomeData>(loadHome, []);
  const [objective, setObjective] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function startMission() {
    const text = objective.trim();
    if (text.length < 8 || busy) return;
    setBusy(true); setErr(null);
    try {
      const created = await founderApi.submitObjective(text);
      await workApi.decomposeAsync(created.project_id);
      navigate(`/projects/${created.project_id}/plan`);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Could not start the mission.");
      setBusy(false);
    }
  }

  const firstName = (user?.full_name || "Founder").split(" ")[0];

  return (
    <div className="wes-page wes-stack">
      {/* ============ CEO Welcome hero ============ */}
      <section className="wes-hero wes-in wes-in-1">
        <div className="wes-eyebrow" style={{ marginBottom: 14 }}>Founder Home</div>
        <h1 className="wes-display" style={{ maxWidth: 720 }}>
          {greeting()}, <span className="wes-grad-text">{firstName}</span>.
        </h1>
        <p className="wes-muted" style={{ fontSize: "var(--wes-fs-lg)", maxWidth: 640, marginTop: 12 }}>
          {loading ? "Bringing your company up to date…" : welcomeLine(data)}
        </p>
        {data && data.evolution.top_opportunities[0] && (
          <div className="wes-row" style={{ marginTop: 18, flexWrap: "wrap" }}>
            <Badge tone="info" dot>Today's recommendation</Badge>
            <span className="wes-muted">{data.evolution.top_opportunities[0].recommendation}</span>
          </div>
        )}
      </section>

      {/* ============ Mission Input — the primary action ============ */}
      <section className="wes-card pad wes-in wes-in-2" aria-label="Start a mission">
        <div className="wes-h2" style={{ marginBottom: 4 }}>What would you like the company to build today?</div>
        <p className="wes-dim" style={{ marginBottom: 16 }}>Describe it as a business goal. Your AI company handles everything else.</p>
        <textarea
          className="wes-textarea" rows={3} value={objective}
          placeholder="e.g. A booking system for a dental clinic with reminders and online payments…"
          onChange={(e) => setObjective(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) startMission(); }}
        />
        <div className="wes-between" style={{ marginTop: 16 }}>
          <span className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)" }}>
            {err ? <span style={{ color: "var(--wes-risk)" }}>{err}</span> : "⌘ + Enter to start"}
          </span>
          <Button variant="primary" size="lg" onClick={startMission} disabled={busy || objective.trim().length < 8}>
            {busy ? "Starting…" : "Start Mission →"}
          </Button>
        </div>
      </section>

      {loading && <HomeSkeleton />}
      {error && <Card><Empty icon="⚠" title="Couldn't reach the company" hint={error} /><div style={{ textAlign: "center" }}><Button onClick={reload}>Retry</Button></div></Card>}

      {data && (
        <>
          {/* ============ Current Mission ============ */}
          <section className="wes-in wes-in-3">
            <SectionTitle title="Current Mission" hint="What the company is working on now" />
            {data.current ? <CurrentMission m={data.current} onOpen={() => data.currentId && navigate(`/projects/${data.currentId}/plan`)} />
              : <Card><Empty title="No active mission" hint="Start one above and the company takes it from there." /></Card>}
          </section>

          {/* ============ Executive Status ============ */}
          <section className="wes-in wes-in-4">
            <SectionTitle title="Executive Office" hint="Your AI leadership, live" />
            <div className="wes-scroll-x">
              {EXECUTIVES.map((e) => (
                <ExecCard key={e.role} exec={e} current={data.current} health={data.health} />
              ))}
            </div>
          </section>

          {/* ============ Company Health ============ */}
          <section className="wes-in wes-in-5">
            <SectionTitle title="Company Health" hint={data.health.note ?? undefined} />
            <div className="wes-grid cols-4">
              <HealthTile label="Overall" value={fmtScore(data.health.company_health_score)} tone={healthTone(data.health.overall)}
                why={`The company is ${data.health.overall ?? "operating"}.`} big />
              <HealthTile label="Delivery quality" value={label(data.health.quality_health)} tone={healthTone(data.health.quality_health)}
                why="Review board & quality gates on every change." />
              <HealthTile label="Deployment" value={label(data.health.deployment_health)} tone={healthTone(data.health.deployment_health)}
                why="Releases pass through staging validation." />
              <HealthTile label="Knowledge & memory" value={label(data.health.knowledge_health)} tone={healthTone(data.health.knowledge_health)}
                why="The company remembers and reuses past work." />
            </div>
          </section>

          {/* ============ Today's Decisions ============ */}
          <section className="wes-in wes-in-6">
            <SectionTitle title="Today's Decisions" hint="Only what needs your authority" />
            {data.decisions.length ? (
              <div className="wes-stack">
                {data.decisions.slice(0, 4).map((d, i) => <DecisionCard key={i} d={d} onGo={() => d.project_id && navigate(`/projects/${d.project_id}/plan`)} />)}
              </div>
            ) : <Card><Empty icon="✓" title="You're all caught up" hint="No decisions need you right now." /></Card>}
          </section>

          {/* ============ Recent Activity + Evolution ============ */}
          <div className="wes-grid cols-2 wes-in">
            <section>
              <SectionTitle title="Recent Activity" />
              <Card>
                {data.activity.length ? (
                  <div className="wes-timeline">
                    {data.activity.map((a, i) => (
                      <div key={i} className={`wes-tl-item${a.outcome === "done" ? " done" : ""}`}>
                        <div style={{ fontWeight: 560 }}>{a.activity}</div>
                        <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)" }}>{narrate(a.outcome)}</div>
                      </div>
                    ))}
                  </div>
                ) : <Empty title="Nothing yet" hint="Activity appears as the company works." />}
              </Card>
            </section>

            <section>
              <SectionTitle title="Company Evolution" />
              <Card>
                <div className="wes-between" style={{ marginBottom: 16 }}>
                  <div>
                    <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)" }}>Evolution score</div>
                    <div className="wes-h1">{data.evolution.company_evolution_score}</div>
                  </div>
                  <ProgressRing value={data.evolution.company_evolution_score} />
                </div>
                <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)", marginBottom: 10 }}>What the company wants to improve</div>
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  {data.evolution.top_opportunities.slice(0, 3).map((o, i) => (
                    <div key={i} className="wes-row" style={{ alignItems: "flex-start", gap: 10 }}>
                      <Badge tone={o.priority === "high" || o.priority === "critical" ? "risk" : "warn"}>{o.priority}</Badge>
                      <span style={{ fontSize: "var(--wes-fs-sm)" }}>{o.recommendation}</span>
                    </div>
                  ))}
                  {!data.evolution.top_opportunities.length && <Empty title="Fully optimised" />}
                </div>
              </Card>
            </section>
          </div>
        </>
      )}
    </div>
  );
}

/* ---------------- sub-components ---------------- */

function SectionTitle({ title, hint }: { title: string; hint?: string }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <div className="wes-h2">{title}</div>
      {hint && <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)", marginTop: 2 }}>{hint}</div>}
    </div>
  );
}

function CurrentMission({ m, onOpen }: { m: MissionDashboard; onOpen: () => void }) {
  return (
    <Card hover className="" style={{ cursor: "pointer" }}>
      <div onClick={onOpen}>
        <div className="wes-between" style={{ alignItems: "flex-start", gap: 20, flexWrap: "wrap" }}>
          <div style={{ minWidth: 260, flex: 1 }}>
            <div className="wes-row" style={{ marginBottom: 10, flexWrap: "wrap" }}>
              <Badge tone={stageTone(m.current_stage)} dot>{m.current_stage}</Badge>
              {m.explanation?.founder_action_required && <Badge tone="warn">Needs your approval</Badge>}
            </div>
            <div className="wes-h2" style={{ marginBottom: 6 }}>{m.mission_name}</div>
            <p className="wes-muted" style={{ maxWidth: 560 }}>{m.current_activity}</p>
            <div className="wes-row" style={{ marginTop: 14, gap: 8 }}>
              <span className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)" }}>{m.current_executive} is leading</span>
              <Thinking />
            </div>
          </div>
          <ProgressRing value={m.overall_progress} />
        </div>

        <div style={{ margin: "20px 0 4px" }}><ProgressBar value={m.overall_progress} /></div>

        <div className="wes-grid cols-3" style={{ marginTop: 18 }}>
          <Meta label="Risk" value={m.current_risk ?? "None flagged"} tone={m.current_risk ? "warn" : "ok"} />
          <Meta label="Expected" value={m.expected_completion} />
          <Meta label="Business stage" value={m.current_stage} />
        </div>
      </div>
    </Card>
  );
}

function Meta({ label, value, tone }: { label: string; value: string; tone?: Tone }) {
  return (
    <div>
      <div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)", textTransform: "uppercase", letterSpacing: ".1em" }}>{label}</div>
      <div style={{ marginTop: 4, color: tone === "warn" ? "var(--wes-warn)" : tone === "ok" ? "var(--wes-ok)" : "var(--wes-text)", fontWeight: 540, fontSize: "var(--wes-fs-sm)" }}>{value}</div>
    </div>
  );
}

function ExecCard({ exec, current, health }:
  { exec: { role: string; focus: string; key: string }; current?: MissionDashboard; health: CompanyHealth }) {
  const active = current?.current_executive
    ? current.current_executive.toLowerCase().includes(exec.role.toLowerCase()) ||
      (exec.role === "Engineering" && current.current_executive.toLowerCase().includes("engineer")) ||
      (exec.role === "CEO" && current.current_executive.toLowerCase().includes("ceo"))
    : false;
  const conf = active ? Math.round((current?.current_confidence ?? 0.7) * 100) : undefined;
  return (
    <Card className="" style={{ minWidth: 208, flex: "0 0 208px" }}>
      <div className="wes-between" style={{ marginBottom: 12 }}>
        <div className="wes-avatar" style={{ background: active ? "var(--wes-accent-grad)" : "var(--wes-bg-4)", color: active ? "#0b0d14" : "var(--wes-text-3)" }}>
          {exec.role.split(" ").map((s) => s[0]).slice(0, 2).join("")}
        </div>
        {active
          ? <Badge tone="info" dot>Working</Badge>
          : <Badge tone={healthTone(health.executive_confidence)}>Ready</Badge>}
      </div>
      <div style={{ fontWeight: 620 }}>{exec.role}</div>
      <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)", marginTop: 2 }}>{exec.focus}</div>
      <div style={{ marginTop: 14, minHeight: 22 }}>
        {active ? (
          <div className="wes-row"><span className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>{conf}% confident</span><Thinking /></div>
        ) : <span className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>Standing by</span>}
      </div>
    </Card>
  );
}

function HealthTile({ label, value, tone, why, big }:
  { label: string; value: string; tone: Tone; why: string; big?: boolean }) {
  return (
    <Card className="" style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      <div className="wes-between">
        <span className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)" }}>{label}</span>
        <span className={`wes-dot`} style={{ color: `var(--wes-${tone === "neutral" ? "info" : tone})` }} />
      </div>
      <div className={big ? "wes-h1" : "wes-h3"} style={{ marginTop: 2 }}>{value}</div>
      <div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)", lineHeight: 1.5 }}>{why}</div>
    </Card>
  );
}

function DecisionCard({ d, onGo }: { d: FounderDecision; onGo: () => void }) {
  return (
    <Card className="">
      <div className="wes-between" style={{ gap: 16, flexWrap: "wrap" }}>
        <div style={{ minWidth: 240, flex: 1 }}>
          <div className="wes-row" style={{ marginBottom: 6 }}>
            <Badge tone="info">{prettyKind(d.kind)}</Badge>
            {d.project && <span className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>{d.project}</span>}
          </div>
          <div style={{ fontWeight: 580 }}>{d.title}</div>
          {d.why && <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)", marginTop: 4 }}>{d.why}</div>}
        </div>
        <div className="wes-row">
          <Button variant="quiet" size="sm" onClick={onGo}>Discuss</Button>
          <Button variant="ok" size="sm" onClick={onGo}>Review &amp; Approve</Button>
        </div>
      </div>
    </Card>
  );
}

function HomeSkeleton() {
  return (
    <div className="wes-stack">
      <Card><Skeleton h={22} w="40%" /><div style={{ marginTop: 14 }}><Skeleton h={80} /></div></Card>
      <div className="wes-grid cols-4">{[0, 1, 2, 3].map((i) => <Card key={i}><Skeleton h={54} /></Card>)}</div>
    </div>
  );
}

/* ---------------- helpers ---------------- */
function welcomeLine(d: HomeData | null): string {
  if (!d) return "";
  const active = d.missions.missions.filter((m) => m.status !== "Completed").length;
  const done = d.missions.missions.length - active;
  const decisions = d.decisions.length;
  // Calm, human phrasing — magnitude over exact counts, one clear call to attention.
  const scale = active === 0 ? "Your company is quiet" : active <= 3 ? `${active} mission${active === 1 ? "" : "s"} in progress` : "Your company is busy across several missions";
  const lead = done > 0 ? `${scale}, and ${done} delivered while you were away.` : `${scale}.`;
  const call = decisions === 0 ? "Nothing needs your attention right now." : decisions === 1 ? "One decision is waiting for you." : `${decisions} decisions are waiting for you.`;
  return `${lead} ${call}`;
}
function fmtScore(v?: number | null) { return v == null ? "—" : `${Math.round(v)}%`; }
function label(v?: string | null) { return v ? v.charAt(0).toUpperCase() + v.slice(1) : "—"; }
function prettyKind(k: string) {
  return ({ approve_project_plan: "Approve plan", approve_pull_request: "Approve release",
    approve_production_deployment: "Approve deployment", resolve_company_degradation: "Resolve issue" } as Record<string, string>)[k]
    ?? k.replace(/_/g, " ");
}
function narrate(outcome: string) {
  return ({ done: "Completed", "needed rework": "Sent back for improvement", "in progress": "Underway" } as Record<string, string>)[outcome] ?? outcome;
}

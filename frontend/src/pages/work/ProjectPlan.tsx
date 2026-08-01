import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { workApi, type ProjectPlan as Plan } from "../../api/work";
import { ErrorNotice, Loading } from "../../components/States";
import { StatusBadge } from "../../components/StatusBadge";
import { SectionCard, StatCard } from "../../components/widgets";
import { useAsync } from "../../hooks/useAsync";

/** AI CEO Analysis — the business analysis and automatic decomposition produced
 * for a Founder intake, with the Founder's plan-approval action. */
export function ProjectPlan() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  // Planning runs in the background (local CPU inference, minutes). Poll the
  // project's plan_status and show live progress instead of a frozen page.
  const [planStatus, setPlanStatus] = useState<string | null>(null);
  const [planError, setPlanError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const startedRef = useRef(Date.now());

  useEffect(() => {
    let alive = true;
    const tick = setInterval(() => setElapsed(Math.floor((Date.now() - startedRef.current) / 1000)), 1000);
    async function poll() {
      try {
        const p = (await workApi.project(id)).data;
        if (!alive) return;
        setPlanStatus(p.plan_status ?? null);
        setPlanError(p.plan_error ?? null);
      } catch {
        /* transient — keep polling */
      }
    }
    poll();
    const iv = setInterval(poll, 5000);
    return () => {
      alive = false;
      clearInterval(iv);
      clearInterval(tick);
    };
  }, [id]);

  const ready = planStatus === "decomposed" || planStatus === "approved";

  // While the AI CEO is still planning (or status not yet known), show progress.
  if (planStatus === "planning" || planStatus === null) {
    const mins = Math.floor(elapsed / 60);
    const secs = elapsed % 60;
    return (
      <div className="page-header" style={{ flexDirection: "column", alignItems: "flex-start", gap: 16 }}>
        <h1>AI CEO is analysing your objective…</h1>
        <p>
          The AI company is reasoning about your business objective, deciding the
          architecture, and building the plan (milestones, sprints, tasks, risks).
          This runs on local AI and typically takes <strong>a few minutes</strong>.
        </p>
        <p>⏱️ Elapsed: <strong>{mins}m {secs}s</strong> — you can safely leave this page and come back; planning continues in the background.</p>
        <Loading label="Planning in progress…" />
        <button className="btn" onClick={() => navigate("/projects")}>Back to Projects</button>
      </div>
    );
  }
  if (planStatus === "failed") {
    return (
      <div>
        <ErrorNotice message={`Planning failed: ${planError || "unknown error"}`} />
        <button className="btn" disabled={busy}
          onClick={() => { setPlanStatus("planning"); startedRef.current = Date.now();
            workApi.decomposeAsync(id).catch(() => setPlanStatus("failed")); }}>
          Retry planning
        </button>
      </div>
    );
  }
  return <PlanView id={id} busy={busy} setBusy={setBusy} msg={msg} setMsg={setMsg} ready={ready} />;
}

/** Renders the completed plan (business analysis + approval action). */
function PlanView(props: {
  id: string; busy: boolean; setBusy: (b: boolean) => void;
  msg: string | null; setMsg: (m: string | null) => void; ready: boolean;
}) {
  const { id, busy, setBusy, msg, setMsg } = props;
  const { data, loading, error, reload } = useAsync<Plan>(
    () => workApi.plan(id).then((r) => r.data),
    [id],
  );

  if (loading) return <Loading label="Loading AI CEO analysis…" />;
  if (error) return <ErrorNotice message={error} />;
  if (!data) return null;

  const a = data.business_analysis;
  const approved = data.project.plan_status === "approved";

  async function act(fn: () => Promise<unknown>, done: string) {
    setBusy(true);
    setMsg(null);
    try {
      await fn();
      setMsg(done);
      reload();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : "Action failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>AI CEO Analysis — {data.project.name}</h1>
          <p>
            {data.project.code} · Analysed by{" "}
            <strong>{a?.analyst ?? "AI CEO"}</strong> · plan{" "}
            <StatusBadge status={approved ? "active" : "onboarding"} />
          </p>
        </div>
        <div className="quick-actions">
          {!approved && (
            <button
              className="btn"
              disabled={busy}
              onClick={() => act(() => workApi.decompose(id), "Re-analysed by the AI CEO.")}
            >
              Re-run Analysis
            </button>
          )}
          <button
            className="btn btn-primary"
            disabled={busy || approved}
            onClick={() => act(() => workApi.approvePlan(id), "Plan approved.")}
          >
            {approved ? "Plan Approved" : "Approve Plan"}
          </button>
        </div>
      </div>

      {msg && <div className="form-note">{msg}</div>}

      {data.project.business_objective && (
        <SectionCard title="Business Objective">
          <p>{data.project.business_objective}</p>
        </SectionCard>
      )}

      {a && (
        <SectionCard title="Business Analysis (AI CEO)">
          <div className="field">
            <label>Vision</label>
            <p>{a.vision}</p>
          </div>
          <div className="cmd-split">
            <div>
              <div className="cmd-subhead">In Scope</div>
              <ul className="plain-list">
                {a.scope.in_scope.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
            <div>
              <div className="cmd-subhead">Out of Scope</div>
              <ul className="plain-list">
                {a.scope.out_of_scope.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
          </div>
          <div className="field" style={{ marginTop: 12 }}>
            <label>Risks</label>
            <ul className="plain-list">
              {a.risks.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          </div>
          <div className="field">
            <label>Architecture Proposal</label>
            <p>{a.architecture_proposal}</p>
          </div>
        </SectionCard>
      )}

      <div className="grid stats" style={{ marginBottom: 16 }}>
        <StatCard label="Epics" value={data.totals.epics} />
        <StatCard label="Sprints" value={data.totals.sprints} />
        <StatCard label="Tasks" value={data.totals.tasks} />
        <StatCard label="Estimated Hours" value={data.totals.estimated_hours} />
      </div>

      <SectionCard
        title="Decomposition"
        action={
          <Link to={`/projects/${id}`} className="btn btn-sm">
            Open Project
          </Link>
        }
      >
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Task</th>
                <th>Title</th>
                <th>Assignee</th>
                <th>Reviewer</th>
                <th>Est. h</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {data.tasks.map((t) => (
                <tr key={t.task_code}>
                  <td>{t.task_code}</td>
                  <td>{t.title}</td>
                  <td>{t.assignee ?? "—"}</td>
                  <td className="muted">{t.reviewer ?? "—"}</td>
                  <td>{t.estimated_hours ?? "—"}</td>
                  <td>
                    <StatusBadge status={t.status === "backlog" ? "onboarding" : "active"} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SectionCard>
    </div>
  );
}

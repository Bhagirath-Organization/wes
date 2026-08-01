import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  founderApi, type FactoryDelivery, type FactoryDependencies, type FactoryFloor,
  type FactoryPipeline, type FactoryPortfolio, type FactoryProduct, type FactoryQuality,
  type FactoryReleases,
} from "../api/founder";
import { Badge, Card, Empty, Icon, ProgressBar, Skeleton, Thinking } from "../components/ui/kit";

type Tab = "pipeline" | "quality" | "releases" | "dependencies" | "portfolio";
const FOUNDER_ACTIONS = ["Approve Release", "Delay Release", "Request Executive Review", "Prioritise Product", "Pause Initiative"];

function pct(v: number | null | undefined): number {
  if (v == null) return 0;
  return v <= 1 ? Math.round(v * 100) : Math.round(v);
}

export function SoftwareFactory() {
  const navigate = useNavigate();
  const [pipeline, setPipeline] = useState<FactoryPipeline | null>(null);
  const [delivery, setDelivery] = useState<FactoryDelivery | null>(null);
  const [floor, setFloor] = useState<FactoryFloor | null>(null);
  const [tab, setTab] = useState<Tab>("pipeline");

  useEffect(() => {
    const load = () => {
      founderApi.factoryProducts().then(setPipeline).catch(() => {});
      founderApi.factoryDelivery().then(setDelivery).catch(() => {});
      founderApi.factoryFloor().then(setFloor).catch(() => {});
    };
    load();
    const iv = setInterval(load, 15000); // the factory floor is live
    return () => clearInterval(iv);
  }, []);

  return (
    <div className="wes-page wes-stack">
      <section className="wes-brain-hero wes-in wes-in-1">
        <div className="wes-eyebrow" style={{ marginBottom: 8 }}>Software Factory</div>
        <h1 className="wes-h1">Watch your software company deliver products.</h1>
        <p className="wes-dim" style={{ marginTop: 6 }}>Not repositories. Not code. Products — moving through business analysis, building, quality, and release.</p>
        {pipeline && (
          <div className="wes-row" style={{ marginTop: 20, gap: 14, flexWrap: "wrap" }}>
            <span className="wes-row" style={{ gap: 8 }}><span className="wes-live-dot" /><span className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)" }}>{pipeline.active} products in delivery · {pipeline.awaiting_founder} awaiting your approval</span></span>
          </div>
        )}
      </section>

      {/* delivery pipeline rail — the 9 business stages */}
      {delivery && (
        <section className="wes-in wes-in-2">
          <div className="wes-h3" style={{ marginBottom: 12 }}>Delivery Pipeline</div>
          <div className="wes-pipeline-rail">
            {delivery.stages.map((s, i) => (
              <div key={s.stage} className={`wes-pl-stage${s.products ? " has" : ""}`} title={s.blurb}>
                <span className="wes-pl-idx">{i + 1}</span>
                <div className="st">{s.stage}</div>
                <div className="ct">{s.products}</div>
                <div className="bl">{s.blurb}</div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* live factory floor */}
      {floor && (
        <section className="wes-in wes-in-3">
          <div className="wes-between" style={{ marginBottom: 12 }}>
            <div className="wes-h3">Software Factory Floor</div>
            <span className="wes-row" style={{ gap: 6 }}>{floor.live && <span className="wes-live-dot" />}<span className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>{floor.live ? "live" : "quiet"}</span></span>
          </div>
          <div className="wes-floor">
            {floor.stations.map((st, i) => (
              <div key={i} className={`wes-station ${st.state}`}>
                <span className="wes-station-ic"><Icon name="workforce" className="wes-nav-ic" /></span>
                <div><div className="wh">{st.who}</div><div className="ac">{st.activity}</div></div>
                {st.state === "active" && <span style={{ marginLeft: "auto" }}><Thinking /></span>}
              </div>
            ))}
          </div>
        </section>
      )}

      <div className="wes-seg-nav wes-in" style={{ flexWrap: "wrap" }}>
        {([["pipeline", "Product Pipeline"], ["quality", "Quality Center"], ["releases", "Release Center"], ["dependencies", "Dependency Map"], ["portfolio", "Portfolio"]] as const).map(([v, l]) => (
          <button key={v} className={`wes-seg-btn${tab === v ? " active" : ""}`} onClick={() => setTab(v)}>{l}</button>
        ))}
      </div>

      {tab === "pipeline" && <ProductPipeline pipeline={pipeline} onOpen={(id) => navigate(`/missions/${id}`)} onApprove={() => navigate("/command")} />}
      {tab === "quality" && <QualityCenter />}
      {tab === "releases" && <ReleaseCenter onApprove={() => navigate("/command")} />}
      {tab === "dependencies" && <DependencyMap />}
      {tab === "portfolio" && <PortfolioView />}

      {/* Founder controls — business actions only (governance gestures) */}
      <Card className="wes-in">
        <div className="wes-h3" style={{ marginBottom: 6 }}>Founder Controls</div>
        <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)", marginBottom: 12 }}>You direct the business — the company handles the engineering.</div>
        <div className="wes-controls">
          {FOUNDER_ACTIONS.map((a) => (
            <button key={a} className={`wes-btn ${a === "Approve Release" ? "wes-btn-primary" : "wes-btn-ghost"} wes-btn-sm`}
              onClick={() => navigate("/command")}>{a}</button>
          ))}
        </div>
      </Card>
    </div>
  );
}

/* -------------------- product pipeline -------------------- */
function ProductPipeline({ pipeline, onOpen, onApprove }: { pipeline: FactoryPipeline | null; onOpen: (id: string) => void; onApprove: () => void }) {
  if (!pipeline) return <div className="wes-products wes-in">{[0, 1, 2].map((i) => <Card key={i}><Skeleton h={140} /></Card>)}</div>;
  if (!pipeline.products.length) return <Card className="wes-in"><Empty title="No products in the factory yet" hint="Submit a business objective and the company starts building." /></Card>;
  return (
    <div className="wes-products wes-in">
      {pipeline.products.map((p) => <ProductCard key={p.product_id} p={p} onOpen={() => onOpen(p.product_id)} onApprove={onApprove} />)}
    </div>
  );
}

function ProductCard({ p, onOpen, onApprove }: { p: FactoryProduct; onOpen: () => void; onApprove: () => void }) {
  const awaiting = p.founder_approval_status === "Awaiting your approval";
  return (
    <div className="wes-product">
      <div className="wes-between">
        <div style={{ minWidth: 0 }}><div className="pn">{p.product}</div>{p.business_objective && <div className="po">{p.business_objective}</div>}</div>
        <Badge tone={awaiting ? "warn" : p.current_stage === "Learning" ? "ok" : "info"}>{p.current_stage}</Badge>
      </div>
      <div style={{ marginTop: 12 }}><ProgressBar value={p.progress} /></div>
      <div className="wes-product-meta">
        <div className="wes-pm"><div className="l">Executive</div><div className="v">{p.current_executive}</div></div>
        <div className="wes-pm"><div className="l">Confidence</div><div className="v">{p.delivery_confidence != null ? `${pct(p.delivery_confidence)}%` : "—"}</div></div>
        <div className="wes-pm"><div className="l">Expected</div><div className="v">{p.expected_delivery || "In planning"}</div></div>
        <div className="wes-pm"><div className="l">Approval</div><div className="v" style={awaiting ? { color: "var(--wes-warn)" } : undefined}>{p.founder_approval_status}</div></div>
      </div>
      {p.current_risk && <div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)", marginTop: 10 }}>⚠ {p.current_risk}</div>}
      {p.dependencies.length > 0 && <div className="wes-caps">{p.dependencies.map((d, i) => <span key={i} className="wes-chip-sm">{d}</span>)}</div>}
      <div className="wes-row" style={{ gap: 8, marginTop: 14 }}>
        <button className="wes-btn wes-btn-ghost wes-btn-sm" onClick={onOpen}>View delivery →</button>
        {awaiting && <button className="wes-btn wes-btn-primary wes-btn-sm" onClick={onApprove}>Approve</button>}
      </div>
    </div>
  );
}

/* -------------------- quality center -------------------- */
function QualityCenter() {
  const [d, setD] = useState<FactoryQuality | null>(null);
  useEffect(() => { founderApi.factoryQuality().then(setD).catch(() => {}); }, []);
  if (!d) return <Card className="wes-in"><Skeleton h={160} /></Card>;
  const trendTone = d.quality_trend === "improving" ? "ok" : d.quality_trend === "declining" ? "warn" : "neutral";
  return (
    <div className="wes-in wes-stack">
      <div className="wes-factory-kpis">
        <StatCard n={d.products_passing} k="Passing review" tone="ok" />
        <StatCard n={d.products_requiring_attention} k="Need attention" tone={d.products_requiring_attention ? "warn" : undefined} />
        <StatCard n={`${d.review_quality}%`} k="Review quality" />
        <StatCard n={`${d.release_confidence}%`} k="Release confidence" />
      </div>
      <Card>
        <div className="wes-between" style={{ marginBottom: 14 }}><div className="wes-h3">Quality trend</div><Badge tone={trendTone} dot>{d.quality_trend}</Badge></div>
        <MeterRow label="Regression confidence" value={d.regression_confidence} />
        <MeterRow label="Release confidence" value={d.release_confidence} />
        <MeterRow label="Average review score" value={d.average_score} />
        <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)", marginTop: 12 }}>{d.note}{d.reviews_performed ? ` · ${d.reviews_performed} reviews performed.` : ""}</div>
      </Card>
    </div>
  );
}

/* -------------------- release center -------------------- */
function ReleaseCenter({ onApprove }: { onApprove: () => void }) {
  const [d, setD] = useState<FactoryReleases | null>(null);
  useEffect(() => { founderApi.factoryReleases().then(setD).catch(() => {}); }, []);
  if (!d) return <Card className="wes-in"><Skeleton h={160} /></Card>;
  return (
    <div className="wes-in wes-stack">
      <div className="wes-factory-kpis">
        <StatCard n={`${d.business_readiness}%`} k="Business readiness" />
        <StatCard n={`${d.deployment_readiness}%`} k="Deployment readiness" />
        <StatCard n={`${d.rollback_confidence}%`} k="Rollback confidence" tone="ok" />
        <StatCard n={d.upcoming_releases.length} k="Upcoming" />
      </div>
      <div className="wes-grid cols-2">
        <ReleaseList title="Upcoming releases" items={d.upcoming_releases} tone="info" empty="No releases in preparation." />
        <ReleaseList title="Completed releases" items={d.completed_releases} tone="ok" empty="No releases delivered yet." />
      </div>
      {(d.delayed_releases.length > 0 || d.blocked_releases.length > 0) && (
        <Card>
          <div className="wes-h3" style={{ marginBottom: 12 }}>Needs your attention</div>
          {d.delayed_releases.map((r, i) => (
            <div key={`d${i}`} className="wes-att-row" style={{ marginBottom: 8 }}>
              <span className="wes-att-dot warn" />
              <div style={{ flex: 1 }}><div style={{ fontSize: "var(--wes-fs-sm)" }}>{r.release}</div><div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>{r.status}</div></div>
              <button className="wes-btn wes-btn-primary wes-btn-sm" onClick={onApprove}>Approve release</button>
            </div>
          ))}
          {d.blocked_releases.map((r, i) => (
            <div key={`b${i}`} className="wes-att-row" style={{ marginBottom: 8 }}>
              <span className="wes-att-dot risk" />
              <div style={{ flex: 1 }}><div style={{ fontSize: "var(--wes-fs-sm)" }}>{r.release}</div><div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>{r.note || "Blocked"}</div></div>
              <button className="wes-btn wes-btn-ghost wes-btn-sm" onClick={onApprove}>Review</button>
            </div>
          ))}
        </Card>
      )}
      <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)" }}>{d.note}</div>
    </div>
  );
}

function ReleaseList({ title, items, tone, empty }: { title: string; items: { release: string; channel?: string; status: string }[]; tone: "info" | "ok"; empty: string }) {
  return (
    <Card>
      <div className="wes-h3" style={{ marginBottom: 12 }}>{title}</div>
      {items.length ? items.map((r, i) => (
        <div key={i} className="wes-between" style={{ padding: "8px 0", borderBottom: "1px solid var(--wes-line-soft)" }}>
          <span style={{ fontSize: "var(--wes-fs-sm)" }}>{r.release}{r.channel ? ` · ${r.channel}` : ""}</span>
          <Badge tone={tone}>{r.status}</Badge>
        </div>
      )) : <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)" }}>{empty}</div>}
    </Card>
  );
}

/* -------------------- dependency map -------------------- */
function DependencyMap() {
  const [d, setD] = useState<FactoryDependencies | null>(null);
  useEffect(() => { founderApi.factoryDependencies().then(setD).catch(() => {}); }, []);
  if (!d) return <Card className="wes-in"><Skeleton h={160} /></Card>;
  return (
    <div className="wes-in wes-grid cols-2">
      <Card>
        <div className="wes-h3" style={{ marginBottom: 12 }}>Shared business capabilities</div>
        {d.shared_capabilities.length ? d.shared_capabilities.map((c, i) => (
          <div key={i} className="wes-dep-cap">
            <span className="wes-dep-bubble">{c.capability}</span>
            <span className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>reused across {c.used_by.length} products</span>
          </div>
        )) : <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)" }}>Each product currently stands alone.</div>}
        {d.knowledge_reuse.reuse_rate != null && (
          <div className="wes-dim" style={{ fontSize: "var(--wes-fs-sm)", marginTop: 14 }}>Knowledge reuse: <strong style={{ color: "var(--wes-text)" }}>{pct(d.knowledge_reuse.reuse_rate)}%</strong>. {d.knowledge_reuse.note}</div>
        )}
      </Card>
      <Card>
        <div className="wes-h3" style={{ marginBottom: 12 }}>Products & executive ownership</div>
        {d.products.slice(0, 10).map((p, i) => (
          <div key={i} className="wes-know-item">
            <div className="wes-between"><span style={{ fontSize: "var(--wes-fs-sm)", fontWeight: 560, minWidth: 0 }}>{p.product}</span><span className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)", flex: "none" }}>{p.executive_owner}</span></div>
            {p.risk && <div className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)", marginTop: 3 }}>⚠ {p.risk}</div>}
          </div>
        ))}
      </Card>
    </div>
  );
}

/* -------------------- portfolio -------------------- */
function PortfolioView() {
  const [d, setD] = useState<FactoryPortfolio | null>(null);
  useEffect(() => { founderApi.factoryPortfolio().then(setD).catch(() => {}); }, []);
  if (!d) return <Card className="wes-in"><Skeleton h={160} /></Card>;
  const cols: [string, FactoryPortfolio["active"]][] = [
    ["Active", d.active], ["Planned", d.planned], ["Completed", d.completed], ["Paused", d.paused], ["Cancelled", d.cancelled],
  ];
  return (
    <div className="wes-in wes-stack">
      <div className="wes-factory-kpis">
        <StatCard n={d.summary.Active} k="Active products" />
        <StatCard n={d.business_value_delivered} k="Delivered" tone="ok" />
        <StatCard n={`${d.strategic_alignment}%`} k="Strategic alignment" />
        <StatCard n={d.summary.Planned} k="Planned" />
      </div>
      <div className="wes-op-cols">
        {cols.filter(([, items]) => items.length).map(([label, items]) => (
          <div key={label}>
            <div className="wes-op-col-head"><span style={{ fontWeight: 600, fontSize: "var(--wes-fs-sm)" }}>{label}</span><span className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>{items.length}</span></div>
            {items.slice(0, 6).map((p, i) => (
              <div key={i} className="wes-op-item">
                <div className="op">{p.product}</div>
                <div className="ow">{p.business_value}</div>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

/* -------------------- small pieces -------------------- */
function StatCard({ n, k, tone }: { n: number | string; k: string; tone?: "ok" | "warn" }) {
  const color = tone === "ok" ? "var(--wes-ok)" : tone === "warn" ? "var(--wes-warn)" : undefined;
  return <div className="wes-op-stat"><div className="n" style={{ color }}>{n}</div><div className="k">{k}</div></div>;
}
function MeterRow({ label, value }: { label: string; value: number }) {
  return (
    <div style={{ marginBottom: 12 }}>
      <div className="wes-between" style={{ marginBottom: 5 }}><span style={{ fontSize: "var(--wes-fs-sm)" }}>{label}</span><span className="wes-dim" style={{ fontSize: "var(--wes-fs-xs)" }}>{value}%</span></div>
      <ProgressBar value={value} />
    </div>
  );
}

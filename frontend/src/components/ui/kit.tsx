/* WES UI kit — reusable primitives built on the design system (wes.css).
   Every screen inherits these; no per-page styling drift. */
import type { CSSProperties, ReactNode } from "react";

/* ---- status helpers ---------------------------------------------------- */
export type Tone = "ok" | "warn" | "risk" | "info" | "neutral";

export function healthTone(v?: string | null): Tone {
  if (!v) return "neutral";
  const s = String(v).toLowerCase();
  if (["healthy", "ok", "active", "released", "completed", "good"].some((k) => s.includes(k))) return "ok";
  if (["degraded", "failed", "risk", "critical", "down"].some((k) => s.includes(k))) return "risk";
  if (["attention", "warn", "pending", "changes", "developing"].some((k) => s.includes(k))) return "warn";
  return "info";
}

export function Badge({ tone = "neutral", dot, children }: { tone?: Tone; dot?: boolean; children: ReactNode }) {
  return (
    <span className={`wes-badge ${tone}`}>
      {dot && <span className="wes-dot" />}
      {children}
    </span>
  );
}

export function Button({
  variant = "ghost", size, onClick, disabled, type = "button", children, style,
}: {
  variant?: "primary" | "ghost" | "quiet" | "ok" | "risk";
  size?: "sm" | "lg"; onClick?: () => void; disabled?: boolean;
  type?: "button" | "submit"; children: ReactNode; style?: CSSProperties;
}) {
  const cls = `wes-btn wes-btn-${variant}${size ? ` wes-btn-${size}` : ""}`;
  return (
    <button type={type} className={cls} onClick={onClick} disabled={disabled} style={style}>
      {children}
    </button>
  );
}

export function Card({ children, className = "", hover, style, onClick }: { children: ReactNode; className?: string; hover?: boolean; style?: CSSProperties; onClick?: () => void }) {
  // When interactive, expose proper button semantics + keyboard operation (a11y).
  const interactive = typeof onClick === "function";
  return (
    <div
      className={`wes-card pad${hover ? " hover" : ""} ${className}`}
      style={style}
      onClick={onClick}
      role={interactive ? "button" : undefined}
      tabIndex={interactive ? 0 : undefined}
      onKeyDown={interactive ? (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onClick!(); } } : undefined}
    >
      {children}
    </div>
  );
}

export function ProgressBar({ value }: { value: number }) {
  return <div className="wes-bar"><span style={{ width: `${Math.max(0, Math.min(100, value))}%` }} /></div>;
}

export function ProgressRing({ value }: { value: number }) {
  const p = Math.max(0, Math.min(100, value));
  return (
    <div className="wes-ring" style={{ ["--p" as string]: p } as CSSProperties}>
      <b>{Math.round(p)}<span style={{ fontSize: ".6rem", opacity: .6 }}>%</span></b>
    </div>
  );
}

export function Thinking() {
  return <span className="wes-think" aria-label="thinking"><i /><i /><i /></span>;
}

export function Skeleton({ h = 16, w = "100%", r }: { h?: number; w?: number | string; r?: number }) {
  return <div className="wes-skel" style={{ height: h, width: w, borderRadius: r ?? 10 }} />;
}

export function Empty({ icon = "✦", title, hint }: { icon?: string; title: string; hint?: string }) {
  return (
    <div className="wes-empty">
      <div className="wes-empty-ic">{icon}</div>
      <div style={{ fontWeight: 620, color: "var(--wes-text-2)" }}>{title}</div>
      {hint && <div style={{ fontSize: "var(--wes-fs-sm)", marginTop: 6 }}>{hint}</div>}
    </div>
  );
}

/* ---- minimal, original line-icon set (no external deps) ---------------- */
type IconProps = { name: string; className?: string };
const P: Record<string, string> = {
  home: "M3 10.5 12 3l9 7.5M5 9.5V21h14V9.5M9.5 21v-6h5v6",
  office: "M4 21V6l8-3 8 3v15M4 21h16M9 9h1.5M9 13h1.5M13.5 9H15M13.5 13H15M10 21v-4h4v4",
  missions: "M4 6h16M4 12h16M4 18h9M18 16l2 2 3-3.5",
  inbox: "M4 13l2.5-8h11L20 13M4 13v6h16v-6M4 13h5l1 2h4l1-2h5",
  company: "M4 21V4h9v17M13 21h7V9h-7M7 8h2M7 12h2M7 16h2M16 12h1.5M16 16h1.5",
  workforce: "M9 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM3 20a6 6 0 0 1 12 0M17 11a3 3 0 1 0 0-6M15.5 14.5A6 6 0 0 1 21 20",
  knowledge: "M5 4h11a2 2 0 0 1 2 2v14l-4-2-4 2V6a2 2 0 0 0-2-2H5v14",
  analytics: "M4 20V4M4 20h16M8 20v-6M12 20V9M16 20v-9M20 20v-4",
  settings: "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM19.4 12a7.4 7.4 0 0 0-.1-1.4l2-1.5-2-3.4-2.3 1a7.3 7.3 0 0 0-2.4-1.4L14 2h-4l-.6 2.9A7.3 7.3 0 0 0 7 6.3l-2.3-1-2 3.4 2 1.5a7.4 7.4 0 0 0 0 2.8l-2 1.5 2 3.4 2.3-1a7.3 7.3 0 0 0 2.4 1.4L10 22h4l.6-2.9a7.3 7.3 0 0 0 2.4-1.4l2.3 1 2-3.4-2-1.5c.06-.46.1-.93.1-1.4Z",
  spark: "M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5 18 18M18 6l-2.5 2.5M8.5 15.5 6 18",
  factory: "M3 21V10l5 3V10l5 3V10l5 3v8H3M3 21h18M7 21v-4M12 21v-4M17 21v-4M6 7l.5-4h1L8 7",
  bell: "M6 9a6 6 0 0 1 12 0c0 5 2 6 2 6H4s2-1 2-6M10 20a2 2 0 0 0 4 0",
};
export function Icon({ name, className = "wes-nav-ic" }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d={P[name] ?? P.home} />
    </svg>
  );
}

/* Business-stage → soft tone for the lifecycle pills */
export function stageTone(stage: string): Tone {
  const s = stage.toLowerCase();
  if (s.includes("complete") || s.includes("validation")) return "ok";
  if (s.includes("deploy")) return "info";
  if (s.includes("review") || s.includes("test")) return "warn";
  return "info";
}

import { useEffect, useState, type ReactNode } from "react";
import { NavLink, useLocation } from "react-router-dom";

import { useSession } from "../auth/SessionContext";
import { Icon } from "./ui/kit";

/* Project AURORA — Founder-first navigation. Top level is intentionally small
   (Linear-style); every other existing route remains reachable and appears
   contextually inside its section. No route is removed. */
type Nav = { to: string; label: string; icon: string; end?: boolean };

const PRIMARY: Nav[] = [
  { to: "/", label: "Home", icon: "home", end: true },
  { to: "/command", label: "Command Center", icon: "analytics" },
  { to: "/operations", label: "Operations", icon: "workforce" },
  { to: "/factory", label: "Software Factory", icon: "factory" },
  { to: "/executive", label: "Executive Office", icon: "office" },
  { to: "/missions", label: "Missions", icon: "missions" },
  { to: "/notifications", label: "Inbox", icon: "inbox" },
];
const SECONDARY: Nav[] = [
  { to: "/brain", label: "Company Brain", icon: "spark" },
  { to: "/company", label: "Company", icon: "company" },
  { to: "/workforce", label: "AI Workforce", icon: "workforce" },
  { to: "/knowledge-network", label: "Knowledge Network", icon: "knowledge" },
  { to: "/analytics", label: "Analytics", icon: "analytics" },
];
const TERTIARY: Nav[] = [{ to: "/settings/providers", label: "Settings", icon: "settings" }];

const ROLE_LABEL: Record<string, string> = {
  founder: "Founder", director: "Director", department_head: "Department Head",
  employee: "Employee", read_only: "Read Only",
};

function NavItem({ item }: { item: Nav }) {
  return (
    <NavLink to={item.to} end={item.end}
      className={({ isActive }) => `wes-nav-item${isActive ? " active" : ""}`}>
      <Icon name={item.icon} />
      <span>{item.label}</span>
    </NavLink>
  );
}

export function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useSession();
  const { pathname } = useLocation();
  const [open, setOpen] = useState(false);

  // Activate the design-system base styles for the whole app.
  useEffect(() => {
    document.body.classList.add("wes");
    return () => document.body.classList.remove("wes");
  }, []);
  // Close the mobile drawer on navigation.
  useEffect(() => setOpen(false), [pathname]);

  const initials = (user?.full_name || "W").split(" ").map((s) => s[0]).slice(0, 2).join("").toUpperCase();

  return (
    <div className={`wes-app${open ? " nav-open" : ""}`}>
      <aside className="wes-side">
        <div className="wes-brand">
          <div className="wes-brand-mark" />
          <div>
            <div className="wes-brand-name">WES</div>
            <span className="wes-brand-sub">AI Company OS</span>
          </div>
        </div>

        <nav className="wes-nav">
          {PRIMARY.map((n) => <NavItem key={n.to} item={n} />)}
          <div className="wes-nav-sec">Company</div>
          {SECONDARY.map((n) => <NavItem key={n.to} item={n} />)}
          <div className="wes-nav-sec">System</div>
          {TERTIARY.map((n) => <NavItem key={n.to} item={n} />)}
        </nav>

        {user && (
          <div className="wes-user">
            <div className="wes-user-row">
              <div className="wes-avatar">{initials}</div>
              <div style={{ minWidth: 0 }}>
                <div className="wes-user-name" style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {user.full_name}
                </div>
                <div className="wes-user-role">{ROLE_LABEL[user.role] ?? user.role}</div>
              </div>
            </div>
            <button className="wes-btn wes-btn-quiet wes-btn-sm" style={{ width: "100%", marginTop: 10, justifyContent: "center" }}
              onClick={() => logout()}>
              Sign out
            </button>
          </div>
        )}
      </aside>

      {open && <div className="wes-scrim" onClick={() => setOpen(false)} />}

      <div className="wes-main">
        <div className="wes-topbar">
          <button className="wes-burger" aria-label="Menu" onClick={() => setOpen((v) => !v)}>☰</button>
          <div className="wes-brand-name">WES</div>
        </div>
        <div className="wes-scroll">{children}</div>
      </div>
    </div>
  );
}

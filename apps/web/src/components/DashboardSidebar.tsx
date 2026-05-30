import { useQuery } from "@tanstack/react-query";
import { Link, NavLink } from "react-router-dom";

import { api } from "../api/client";

export function DashboardSidebar({
  collapsed,
  width,
  onCollapsedChange,
}: {
  collapsed: boolean;
  width: number;
  onCollapsedChange: (collapsed: boolean) => void;
}) {
  const { data: spreads } = useQuery({
    queryKey: ["spreads"],
    queryFn: () => api.listSpreads(false),
  });
  const { data: options } = useQuery({
    queryKey: ["legs", "ungrouped"],
    queryFn: () => api.listLegs(true),
  });
  const { data: allSpreads } = useQuery({
    queryKey: ["spreads", "all"],
    queryFn: () => api.listSpreads(true),
  });
  const { data: allLegs } = useQuery({
    queryKey: ["legs", "all"],
    queryFn: () => api.listLegs(false, true),
  });

  const gainsCount =
    (allSpreads ?? []).filter((s) => s.closed_at != null).length +
    (allLegs ?? []).filter((l) => l.closed_at != null && l.spread_id == null)
      .length;

  return (
    <aside
      className="fixed inset-y-0 left-0 z-20 hidden h-svh flex-col overflow-hidden border-r border-border bg-panel transition-[width] duration-200 ease-linear lg:flex"
      style={{ width }}
    >
      <div
        className={`flex h-[52px] shrink-0 items-center overflow-hidden border-b border-border px-3 ${
          collapsed ? "justify-center" : "justify-between"
        }`}
      >
        <Link
          to="/spreads"
          className={`items-center gap-2 overflow-hidden whitespace-nowrap ${
            collapsed ? "hidden" : "flex"
          }`}
          aria-label="credit-spread"
          title="credit-spread"
        >
          <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg border border-border bg-bg">
            <span className="h-2.5 w-2.5 rounded-full bg-accent" />
          </span>
          <span className="min-w-0 overflow-hidden whitespace-nowrap">
            <span className="block truncate text-sm font-semibold leading-tight tracking-tight">
              credit-spread
            </span>
            <span className="block truncate whitespace-nowrap text-[10px] uppercase tracking-[0.24em] text-muted">
              PnL Platform
            </span>
          </span>
        </Link>
        <button
          type="button"
          className={`grid h-8 w-8 shrink-0 place-items-center rounded-md text-sm text-muted transition hover:bg-bg hover:text-fg ${
            collapsed ? "" : "ml-auto"
          }`}
          onClick={() => onCollapsedChange(!collapsed)}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <span aria-hidden>{collapsed ? ">" : "||"}</span>
        </button>
      </div>

      <div className="min-w-0 px-3 py-4">
        <div className="mb-3 h-4 overflow-hidden whitespace-nowrap px-1 text-[11px] font-medium uppercase leading-4 tracking-[0.24em] text-muted">
          {!collapsed && "Workspace"}
        </div>

        <nav className="space-y-1">
          <DashboardNavItem
            to="/spreads"
            label="Vertical spreads"
            shortLabel="VS"
            count={spreads?.length ?? 0}
            collapsed={collapsed}
          />
          <DashboardNavItem
            to="/options"
            label="Other options"
            shortLabel="OP"
            count={options?.length ?? 0}
            collapsed={collapsed}
          />
          <DashboardNavItem
            to="/gains"
            label="Gains"
            shortLabel="$"
            count={gainsCount}
            collapsed={collapsed}
          />
          <DashboardNavItem
            to="/groupings"
            label="Groupings"
            shortLabel="GR"
            collapsed={collapsed}
          />
        </nav>
      </div>
    </aside>
  );
}

function DashboardNavItem({
  to,
  label,
  shortLabel,
  count,
  collapsed,
}: {
  to: string;
  label: string;
  shortLabel: string;
  count?: number;
  collapsed: boolean;
}) {
  return (
    <NavLink
      to={to}
      aria-label={label}
      title={collapsed ? label : undefined}
      className={({ isActive }) =>
        `flex min-h-9 items-center gap-3 overflow-hidden rounded-md px-3 py-2 text-sm transition ${
          collapsed ? "justify-center" : "justify-between"
        } ${
          isActive ? "bg-bg text-fg" : "text-muted hover:bg-bg/60 hover:text-fg"
        }`
      }
    >
      {collapsed ? (
        <span className="font-mono text-xs">{shortLabel}</span>
      ) : (
        <>
          <span className="min-w-0 truncate whitespace-nowrap">{label}</span>
          {count != null && (
            <span className="shrink-0 font-mono text-xs">{count}</span>
          )}
        </>
      )}
    </NavLink>
  );
}

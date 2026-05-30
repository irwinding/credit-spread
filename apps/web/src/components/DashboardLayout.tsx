import { ReactNode, useEffect, useState } from "react";

import { DashboardSidebar } from "./DashboardSidebar";
import { useTheme } from "../lib/theme";

const STORAGE_KEY = "credit-spread.sidebarCollapsed";

export function DashboardLayout({ children }: { children: ReactNode }) {
  const [theme, , toggleTheme] = useTheme();
  const [collapsed, setCollapsed] = useState(() => {
    if (typeof window === "undefined") return false;
    return window.localStorage.getItem(STORAGE_KEY) === "true";
  });

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, String(collapsed));
  }, [collapsed]);
  const nextTheme = theme === "dark" ? "light" : "dark";
  const sidebarWidth = collapsed ? 72 : 230;

  return (
    <div className="min-h-screen lg:flex">
      <div
        aria-hidden
        className="hidden shrink-0 transition-[width] duration-200 ease-linear lg:block"
        style={{ width: sidebarWidth }}
      />
      <DashboardSidebar
        collapsed={collapsed}
        width={sidebarWidth}
        onCollapsedChange={setCollapsed}
      />
      <main className="min-w-0 flex-1 px-6 py-6 lg:px-8 lg:py-8">
        <div className="mb-4 flex justify-end">
          <button
            type="button"
            onClick={toggleTheme}
            aria-label={`Switch to ${nextTheme} theme`}
            title={`Switch to ${nextTheme} theme`}
            className="grid h-9 w-9 place-items-center rounded-md border border-border bg-panel text-sm text-muted transition hover:text-fg"
          >
            <span aria-hidden>{theme === "dark" ? "☾" : "☀"}</span>
          </button>
        </div>
        {children}
      </main>
    </div>
  );
}

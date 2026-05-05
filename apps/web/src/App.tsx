import { Link, NavLink, Route, Routes } from "react-router-dom";

import { Dashboard } from "./pages/Dashboard";
import { Groupings } from "./pages/Groupings";
import { SpreadDetail } from "./pages/SpreadDetail";
import { useTheme } from "./lib/theme";

const navClass = ({ isActive }: { isActive: boolean }) =>
  `px-3 py-1.5 rounded-md text-sm transition ${
    isActive
      ? "bg-panel text-fg border border-border"
      : "text-muted hover:text-fg"
  }`;

function ThemeToggle() {
  const [theme, , toggle] = useTheme();
  const isDark = theme === "dark";
  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={`Switch to ${isDark ? "light" : "dark"} theme`}
      title={`Switch to ${isDark ? "light" : "dark"} theme`}
      className="px-2.5 py-1.5 rounded-md text-sm border border-border bg-panel text-muted hover:text-fg transition"
    >
      {isDark ? "☾" : "☀"}
    </button>
  );
}

export function App() {
  return (
    <div className="min-h-full flex flex-col">
      <header className="border-b border-border">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-accent" />
            <span className="font-semibold tracking-tight">credit-spread</span>
          </Link>
          <nav className="flex gap-1 items-center">
            <NavLink to="/" end className={navClass}>
              Dashboard
            </NavLink>
            <NavLink to="/groupings" className={navClass}>
              Groupings
            </NavLink>
            <span className="ml-2">
              <ThemeToggle />
            </span>
          </nav>
        </div>
      </header>
      <main className="flex-1">
        <div className="max-w-6xl mx-auto px-6 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/spread/:id" element={<SpreadDetail />} />
            <Route path="/groupings" element={<Groupings />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}

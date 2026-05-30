import { Link } from "react-router-dom";

import type { Leg, Spread } from "../api/types";
import {
  fmtMoney,
  formatCloseReason,
  formatSpreadType,
} from "../lib/format";
import { optionPnL, optionSideLabel } from "../lib/options";

type GainItem =
  | { kind: "spread"; spread: Spread }
  | { kind: "option"; leg: Leg };

export function GainCard({ item }: { item: GainItem }) {
  if (item.kind === "spread") {
    return <SpreadGainCard spread={item.spread} />;
  }
  return <OptionGainCard leg={item.leg} />;
}

function SpreadGainCard({ spread }: { spread: Spread }) {
  const pnl = spread.last_pnl != null ? Number(spread.last_pnl) : null;
  const pnlClass = pnl == null ? "text-muted" : pnl >= 0 ? "pnl-pos" : "pnl-neg";
  const closedAt = spread.closed_at ? new Date(spread.closed_at) : null;

  return (
    <Link
      to={`/spread/${spread.id}`}
      state={{ from: "/gains", label: "Gains" }}
      className="panel p-4 block hover:border-accent transition"
    >
      <GainHeader
        title={spread.underlying}
        subtitle={formatSpreadType(spread.spread_type)}
        pnl={pnl}
        pnlClass={pnlClass}
      />
      <div className="mt-3 grid grid-cols-3 gap-3 text-xs">
        <Stat label="Short" value={spread.short_strike ?? "—"} />
        <Stat label="Long" value={spread.long_strike ?? "—"} />
        <Stat label="Closed" value={closedAt ? closedAt.toLocaleDateString() : "—"} />
      </div>
      <div className="mt-3 text-[10px] uppercase tracking-wider text-muted">
        {formatCloseReason(spread.close_reason)}
      </div>
    </Link>
  );
}

function OptionGainCard({ leg }: { leg: Leg }) {
  const mid = leg.last_mark != null ? Number(leg.last_mark) : null;
  const pnl = optionPnL(leg, mid);
  const pnlClass = pnl == null ? "text-muted" : pnl >= 0 ? "pnl-pos" : "pnl-neg";
  const closedAt = leg.closed_at ? new Date(leg.closed_at) : null;

  return (
    <Link
      to={`/option/${leg.id}`}
      state={{ from: "/gains", label: "Gains" }}
      className="panel p-4 block hover:border-accent transition"
    >
      <GainHeader
        title={leg.underlying}
        subtitle={optionSideLabel(leg)}
        pnl={pnl}
        pnlClass={pnlClass}
      />
      <div className="mt-3 grid grid-cols-3 gap-3 text-xs">
        <Stat label="Strike" value={leg.strike} />
        <Stat label="Qty" value={String(leg.quantity)} />
        <Stat label="Closed" value={closedAt ? closedAt.toLocaleDateString() : "—"} />
      </div>
      <div className="mt-3 text-[10px] uppercase tracking-wider text-muted">
        {formatCloseReason(leg.close_reason)}
      </div>
    </Link>
  );
}

function GainHeader({
  title,
  subtitle,
  pnl,
  pnlClass,
}: {
  title: string;
  subtitle: string;
  pnl: number | null;
  pnlClass: string;
}) {
  return (
    <div className="flex items-baseline justify-between gap-3">
      <div>
        <div className="text-lg font-semibold tracking-tight">{title}</div>
        <div className="text-xs text-muted">{subtitle}</div>
      </div>
      <div className={`font-mono text-sm ${pnlClass}`}>
        {pnl == null ? "—" : fmtMoney(pnl)}
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="stat">{label}</div>
      <div className="font-mono">{value}</div>
    </div>
  );
}

import { Link } from "react-router-dom";

import type { Spread } from "../api/types";
import { fmtMoney, formatSpreadType, daysUntil } from "../lib/format";

interface Props {
  spread: Spread;
}

export function SpreadCard({ spread }: Props) {
  const dte = daysUntil(spread.expiry);
  const pnlNum = spread.last_pnl != null ? Number(spread.last_pnl) : null;
  const pnlClass =
    pnlNum == null ? "text-muted" : pnlNum >= 0 ? "pnl-pos" : "pnl-neg";
  const lastTs = spread.last_snapshot_at
    ? new Date(spread.last_snapshot_at)
    : null;

  return (
    <Link
      to={`/spread/${spread.id}`}
      className="panel p-4 block hover:border-accent transition"
    >
      <div className="flex items-baseline justify-between">
        <div>
          <div className="text-lg font-semibold tracking-tight">
            {spread.underlying}
          </div>
          <div className="text-xs text-muted">
            {formatSpreadType(spread.spread_type)} · {dte}d to expiry
          </div>
        </div>
        <div className="text-right">
          <div className={`font-mono text-sm ${pnlClass}`}>
            {pnlNum == null ? "—" : fmtMoney(pnlNum)}
          </div>
          <div className="text-[10px] text-muted">
            {lastTs
              ? `as of ${lastTs.toLocaleString([], {
                  month: "short",
                  day: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })}`
              : "no snapshot yet"}
          </div>
        </div>
      </div>
      <div className="mt-3 grid grid-cols-3 gap-3 text-xs">
        <Stat label="Short" value={spread.short_strike ?? "—"} />
        <Stat label="Long" value={spread.long_strike ?? "—"} />
        <Stat label="Width" value={spread.width ?? "—"} />
      </div>
      <div className="mt-3 flex gap-2 text-[10px] uppercase tracking-wider">
        {spread.user_locked && (
          <span className="text-accent">locked · manual</span>
        )}
        {spread.stop_loss_breached && (
          <span className="text-red-400">stop loss breached</span>
        )}
      </div>
    </Link>
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

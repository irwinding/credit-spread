import { Link } from "react-router-dom";

import type { Leg } from "../api/types";
import { daysUntil, fmtMoney, formatCloseReason } from "../lib/format";
import { optionCashflow, optionPnL, optionSideLabel } from "../lib/options";

export function OptionCard({ leg }: { leg: Leg }) {
  const dte = daysUntil(leg.expiry);
  const mid = leg.last_mark != null ? Number(leg.last_mark) : null;
  const pnl = optionPnL(leg, mid);
  const pnlClass = pnl == null ? "text-muted" : pnl >= 0 ? "pnl-pos" : "pnl-neg";
  const cashflow = optionCashflow(leg);
  const lastTs = leg.last_mark_ts ? new Date(leg.last_mark_ts) : null;

  return (
    <Link
      to={`/option/${leg.id}`}
      state={{ from: "/options", label: "Other options" }}
      className="panel p-4 block hover:border-accent transition"
    >
      <div className="flex items-baseline justify-between gap-3">
        <div>
          <div className="text-lg font-semibold tracking-tight">
            {leg.underlying}
          </div>
          <div className="text-xs text-muted">
            {optionSideLabel(leg)} · {dte}d to expiry
          </div>
        </div>
        <div className="text-right">
          <div className={`font-mono text-sm ${pnlClass}`}>
            {pnl == null ? "—" : fmtMoney(pnl)}
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
        <Stat label="Strike" value={leg.strike} />
        <Stat label="Qty" value={String(leg.quantity)} />
        <Stat label="Mid" value={mid == null ? "—" : mid.toFixed(2)} />
      </div>
      <div className="mt-3 text-[10px] uppercase tracking-wider text-muted">
        Entry {leg.entry_price ?? "—"} ·{" "}
        {cashflow == null ? "cashflow —" : `cashflow ${fmtMoney(cashflow)}`}
        {leg.closed_at && <> · {formatCloseReason(leg.close_reason)}</>}
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

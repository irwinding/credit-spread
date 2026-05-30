import { useQuery } from "@tanstack/react-query";
import { Link, useLocation, useParams } from "react-router-dom";

import { api } from "../api/client";
import { PnLChart } from "../components/PnLChart";
import { daysUntil, fmtMoney } from "../lib/format";
import {
  legHistoryToPnLPoints,
  optionCashflow,
  optionPnL,
  optionSideLabel,
} from "../lib/options";

export function OptionDetail() {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const legId = id ? Number(id) : NaN;

  const { data: legs = [] } = useQuery({
    queryKey: ["legs", "all"],
    queryFn: () => api.listLegs(false, true),
  });
  const { data: history } = useQuery({
    queryKey: ["leg", legId, "history"],
    queryFn: () => api.getLegHistory(legId),
    enabled: Number.isFinite(legId),
  });

  const leg = legs.find((l) => l.id === legId);
  if (!leg) {
    return <div className="text-muted">Loading…</div>;
  }

  const latestMid = leg.last_mark != null ? Number(leg.last_mark) : null;
  const pnl = optionPnL(leg, latestMid);
  const pnlClass = pnl == null ? "text-muted" : pnl >= 0 ? "pnl-pos" : "pnl-neg";
  const cashflow = optionCashflow(leg);
  const points = history ? legHistoryToPnLPoints(leg, history.points) : [];
  const backTarget = detailBackTarget(location.state, "/options", "Other options");
  const bidAsk =
    leg.last_bid != null && leg.last_ask != null
      ? `${Number(leg.last_bid).toFixed(2)} / ${Number(leg.last_ask).toFixed(2)}`
      : "—";

  return (
    <div className="space-y-6">
      <Link to={backTarget.from} className="text-sm text-muted hover:text-fg">
        ← {backTarget.label}
      </Link>

      <div className="flex items-baseline justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            {leg.underlying}{" "}
            <span className="text-muted text-base">{optionSideLabel(leg)}</span>
          </h1>
          <p className="text-sm text-muted mt-1">
            {leg.strike} strike · expires {leg.expiry} ({daysUntil(leg.expiry)}d)
          </p>
        </div>
        <div className="text-right">
          <div className="stat">Unrealised PnL</div>
          <div className={`text-2xl font-mono ${pnlClass}`}>
            {pnl == null ? "—" : fmtMoney(pnl)}
          </div>
        </div>
      </div>

      <div className="panel p-4">
        {points.length > 0 ? (
          <PnLChart
            points={points}
            underlying={leg.underlying}
            secondaryLabel="Option mid"
          />
        ) : (
          <div className="text-muted text-sm py-12 text-center">
            No option snapshots yet. Take one from the Dashboard.
          </div>
        )}
      </div>

      <div className="panel p-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Field label="Symbol" value={leg.option_symbol} />
        <Field label="Quantity" value={String(leg.quantity)} />
        <Field label="Entry" value={leg.entry_price ?? "—"} />
        <Field label="Mid" value={latestMid == null ? "—" : latestMid.toFixed(2)} />
        <Field label="Bid / Ask" value={bidAsk} />
        <Field
          label="Credit / Debit"
          value={cashflow == null ? "—" : fmtMoney(cashflow)}
        />
        <Field label="Grouped" value={leg.spread_id == null ? "No" : "Yes"} />
        <Field label="Last mark" value={leg.last_mark_ts ?? "—"} />
      </div>
    </div>
  );
}

function detailBackTarget(
  state: unknown,
  fallbackFrom: string,
  fallbackLabel: string,
) {
  if (
    state &&
    typeof state === "object" &&
    "from" in state &&
    "label" in state &&
    typeof state.from === "string" &&
    typeof state.label === "string"
  ) {
    return { from: state.from, label: state.label };
  }
  return { from: fallbackFrom, label: fallbackLabel };
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0">
      <div className="stat">{label}</div>
      <div className="font-mono text-sm break-words">{value}</div>
    </div>
  );
}

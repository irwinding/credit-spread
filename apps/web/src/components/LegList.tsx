import type { Leg } from "../api/types";

export function LegList({ legs }: { legs: Leg[] }) {
  if (legs.length === 0) {
    return <div className="text-sm text-muted">No legs.</div>;
  }
  return (
    <table className="w-full text-sm font-mono">
      <thead className="text-xs uppercase tracking-wider text-muted">
        <tr className="border-b border-border">
          <th className="text-left py-2">Side</th>
          <th className="text-left py-2">Symbol</th>
          <th className="text-right py-2">Strike</th>
          <th className="text-right py-2">Qty</th>
          <th className="text-right py-2">Entry</th>
          <th className="text-right py-2">Cr/Dr ($)</th>
          <th className="text-right py-2">Mid</th>
          <th className="text-right py-2">Bid/Ask</th>
        </tr>
      </thead>
      <tbody>
        {legs.map((l) => {
          const mark = l.last_mark != null ? Number(l.last_mark) : null;
          const entry = l.entry_price != null ? Number(l.entry_price) : null;
          const markCls =
            mark != null && entry != null
              ? l.quantity < 0
                ? mark < entry
                  ? "pnl-pos"
                  : "pnl-neg"
                : mark > entry
                  ? "pnl-pos"
                  : "pnl-neg"
              : "";
          const bidask =
            l.last_bid != null && l.last_ask != null
              ? `${Number(l.last_bid).toFixed(2)} / ${Number(l.last_ask).toFixed(2)}`
              : "—";
          // Credit (+) when short leg sold, debit (-) when long leg bought.
          const cashflow =
            entry != null ? -l.quantity * entry * 100 : null;
          const cashCls =
            cashflow == null ? "" : cashflow >= 0 ? "pnl-pos" : "pnl-neg";
          return (
            <tr key={l.id} className="border-b border-border/50">
              <td className={`py-2 ${l.quantity < 0 ? "pnl-neg" : "pnl-pos"}`}>
                {l.quantity < 0 ? "SHORT" : "LONG"} {l.option_type}
              </td>
              <td className="py-2 text-xs">{l.option_symbol}</td>
              <td className="py-2 text-right">{l.strike}</td>
              <td className="py-2 text-right">{l.quantity}</td>
              <td className="py-2 text-right">{l.entry_price ?? "—"}</td>
              <td className={`py-2 text-right ${cashCls}`}>
                {cashflow != null
                  ? `${cashflow >= 0 ? "+" : ""}${cashflow.toFixed(2)}`
                  : "—"}
              </td>
              <td className={`py-2 text-right ${markCls}`}>
                {mark != null ? mark.toFixed(2) : "—"}
              </td>
              <td className="py-2 text-right text-xs text-muted">{bidask}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

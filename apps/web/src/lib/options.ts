import type { Leg, LegSnapshotPoint, SnapshotPoint } from "../api/types";

export function optionSideLabel(leg: Leg): string {
  return `${leg.quantity < 0 ? "Short" : "Long"} ${leg.option_type.toLowerCase()}`;
}

export function optionCashflow(leg: Leg): number | null {
  const entry = leg.entry_price != null ? Number(leg.entry_price) : null;
  if (entry == null) return null;
  return -leg.quantity * entry * 100;
}

export function optionPnL(leg: Leg, mid: number | null): number | null {
  const entry = leg.entry_price != null ? Number(leg.entry_price) : null;
  if (entry == null || mid == null) return null;
  return leg.quantity * (mid - entry) * 100;
}

export function legHistoryToPnLPoints(
  leg: Leg,
  points: LegSnapshotPoint[],
): SnapshotPoint[] {
  return points
    .map((p) => {
      const mid = Number(p.mid);
      const pnl = optionPnL(leg, mid);
      if (pnl == null) return null;
      return {
        ts: p.ts,
        spread_mark: p.mid,
        pnl_unrealised: String(pnl),
        underlying_price: p.mid,
      };
    })
    .filter((p): p is SnapshotPoint => p != null);
}

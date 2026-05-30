export type SpreadType = "BULL_PUT" | "BEAR_CALL" | "OTHER";
export type DetectionMode = "AUTO" | "MANUAL";

export interface Leg {
  id: number;
  moomoo_position_id: string;
  underlying: string;
  option_symbol: string;
  option_type: "CALL" | "PUT";
  strike: string;
  expiry: string; // YYYY-MM-DD
  quantity: number;
  entry_price: string | null;
  spread_id: string | null;
  closed_at: string | null;
  close_reason: string | null;
  last_mark: string | null;
  last_bid: string | null;
  last_ask: string | null;
  last_mark_ts: string | null;
}

export interface LegSnapshotPoint {
  ts: string;
  bid: string | null;
  ask: string | null;
  mid: string;
}

export interface LegHistory {
  leg_id: number;
  points: LegSnapshotPoint[];
}

export interface Spread {
  id: string;
  underlying: string;
  expiry: string;
  spread_type: SpreadType;
  short_strike: string | null;
  long_strike: string | null;
  width: string | null;
  quantity: number;
  net_credit: string | null;
  stop_loss_pct: string | null;
  opened_at: string | null;
  closed_at: string | null;
  close_reason: string | null;
  detection_mode: DetectionMode;
  user_locked: boolean;
  legs: Leg[];
  last_pnl: string | null;
  last_spread_mark: string | null;
  last_underlying_price: string | null;
  last_snapshot_at: string | null;
  stop_loss_breached: boolean;
}

export interface SnapshotPoint {
  ts: string;
  spread_mark: string;
  pnl_unrealised: string;
  underlying_price: string;
}

export interface SpreadHistory {
  spread_id: string;
  points: SnapshotPoint[];
}

export interface SnapshotResult {
  rows_written: number;
  ts: string;
}

export interface SnapshotStatus {
  next_run_at: string | null;
  last_snapshot_at: string | null;
  server_time: string;
}

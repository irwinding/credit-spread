# Covered Call support — design

**Date:** 2026-05-27
**Status:** Approved (pending spec review)

## Goal

Track covered-call positions (long shares + short call) alongside credit spreads,
with full P&L (stock gain/loss + call premium), surfaced under a separate
"Covered calls" tab on the dashboard with the same clickable P&L-history detail
view that spreads already have.

## Context

The system currently ingests **option** positions only. `MoomooClient.list_option_positions`
parses each moomoo position code and skips any row where `parse_option_code` fails —
so stock holdings are dropped entirely. A covered call needs the share leg, which is
the central gap.

`OptionLeg` cannot represent stock: `strike`, `expiry`, and `option_type` are NOT NULL
and `option_symbol` is constrained to parse as an option code (and is now `unique`).

**Architecture decision (Approach A):** reuse the existing `Spread` grouping entity and
the entire snapshot/detail/chart pipeline; add a separate `stock_positions` table for the
share leg. A covered call is a `Spread` row with `spread_type="COVERED_CALL"` holding the
short-call `OptionLeg`(s) plus a linked `StockPosition`. The word "Spread" thus means
"position group" internally — kept as-is because renaming touches every file and the DB.
Rejected Approach B (separate `CoveredCall` model + parallel tables/endpoints/detail page)
because it roughly doubles the code for identical behavior.

## Decisions captured from brainstorming

- **Track shares + short call** (full P&L), not the short call alone.
- **One covered-call position per underlying** — group all shares + all short calls on an
  underlying into a single position; report coverage and flag leftovers.
- **Tabs on the dashboard** ("Credit spreads" | "Covered calls"), shared snapshot controls.
- **Clickable detail with P&L history chart**, reusing existing components.

## 1. Data model

New table **`stock_positions`**:

| column | type | notes |
|---|---|---|
| `id` | BigInt PK | autoincrement (SQLite variant Integer) |
| `symbol` | String(64), **unique**, not null | e.g. `US.META` — stable identity (same lesson as the `option_symbol` fix) |
| `underlying` | String(16), not null | `META` |
| `quantity` | Integer, not null | signed share count (long positive) |
| `cost_price` | Numeric(14,4), nullable | average per-share cost |
| `moomoo_position_id` | String(64), not null | mutable metadata, refreshed each snapshot |
| `spread_id` | Uuid FK → `spreads.id`, `ON DELETE SET NULL`, nullable | |
| `closed_at` | DateTime(tz), nullable | |

`Spread`:
- Add relationship `stock_position: Mapped[StockPosition | None]` (one-to-one;
  `StockPosition.spread_id` is the FK side; `uselist=False`).
- `spread_type` accepts the new value `"COVERED_CALL"` (String column, no schema change).

**Migration 0005_stock_positions** (`down_revision = "0004"`): create the table with the
unique constraint on `symbol`. `downgrade` drops the table.

## 2. Ingestion

`MoomooClient`:
- New dataclass `RawStock(moomoo_position_id, symbol, underlying, quantity, cost_price)`.
- New method `list_stock_positions() -> list[RawStock]`: iterate the same
  `position_list_query` rows; a row is a stock when `parse_option_code(code)` raises
  **and** `code` matches `MARKET.TICKER` (`^[A-Z]+\.[A-Z.]+$`). `underlying` is the part
  after the dot. `quantity` signed from `position_side` (LONG positive). `cost_price` from
  `cost_price`/`cost_price`-equivalent field (reuse the `_dec` helper).
- `list_option_positions` is unchanged (still returns only options).

Snapshotter `_upsert_stock_positions(db, raw_stocks)`: match existing by `symbol`; update
`moomoo_position_id`, `quantity`, `cost_price`, clear `closed_at`; insert when absent.
Mirrors the `option_symbol`-keyed `_upsert_legs`.

## 3. Detection

New pure module function (in `spread_detector.py` or a sibling `covered_call_detector.py`):

```
detect_covered_calls(option_legs, stock_positions, locked_leg_ids) -> list[DetectedCoveredCall]
```

`DetectedCoveredCall` dataclass: `underlying`, `expiry` (nearest short-call expiry),
`stock` (the matched stock position input), `call_legs` (list of short-call LegInputs),
`shares`, `covered_contracts`, `uncovered_contracts`, `uncovered_shares`, `net_credit`.

Algorithm — for each underlying:
- Collect long stock (`shares = sum(qty > 0)`) and **short call** legs (`option_type=="CALL"`,
  `quantity < 0`), excluding `locked_leg_ids`.
- Emit a covered call **only if** `shares >= 100` and there is ≥1 short call.
- `total_short_contracts = sum(abs(qty))`; `covered_contracts = min(shares // 100, total_short_contracts)`.
- `uncovered_contracts = max(0, total_short_contracts - shares // 100)` (naked portion).
- `uncovered_shares = max(0, shares - covered_contracts * 100)`.
- `net_credit = Σ(-qty_signed × entry) × 100` over the call legs (premium received), or
  `None` if any entry price is missing.
- A short call with no backing shares is **not** emitted (naked → stays ungrouped).

Ordering in the snapshotter: run `detect_covered_calls` first, then pass the consumed
short-call leg ids into `detect_spreads`'s `locked_leg_ids` so a covered call's short call
can't also be paired into a vertical.

Reconciliation `_upsert_covered_calls(db, detected)`: analogous to `_upsert_auto_spreads` —
find an existing non-locked `Spread` owning this underlying's call legs / stock position,
reuse it (updating `spread_type`, `expiry`, `net_credit` when unset), else create a new
`Spread(spread_type="COVERED_CALL", short_strike=None, long_strike=None, width=None, ...)`.
Then point the call legs' `spread_id` and the stock position's `spread_id` at it.

## 4. P&L

Generalize `_compute_marks(client, spread, quote_cache)`:
- Existing option contribution unchanged: `calls_pnl_per_share = Σ qty_signed × (mid − entry)`;
  `option_value_per_share = Σ qty_signed × mid`.
- If `spread.stock_position` is set and has a cost:
  `stock_pnl = shares × (underlying_price − cost)` (NOT ×100).
- `pnl_dollars = calls_pnl_per_share × 100 + stock_pnl`.
- `spread_mark = -option_value_per_share` (debit to buy back the calls; stock excluded).
- `underlying_price` from `client.get_underlying_price(spread.underlying)` as today.

Stock legs get **no** `LegSnapshot` (no option mid). Only option legs are snapshotted per-leg.
The per-leg quote-cache loop iterates `spread.legs` (options only), so it is unaffected.

## 5. API / schemas

No new endpoints — `/spreads`, `/spreads/{id}`, `/spreads/{id}/history` are reused.

`SpreadOut` additions (all optional, populated in the same attach step that adds latest
snapshot data):
- `stock: StockOut | None` — `{ shares: int, cost: Decimal | None }`
- `covered_contracts: int | None`
- `uncovered_contracts: int | None`
- `uncovered_shares: int | None`

Coverage fields are derived at read time from the stock position + short-call quantities
(same formulas as detection) in a `_attach_covered_call_info(db, spreads)` helper called from
`list_spreads` and `get_spread`.

## 6. Frontend

- **`types.ts`**: `SpreadType` gains `"COVERED_CALL"`; `Spread` gains optional
  `stock: { shares: number; cost: string | null } | null`, `covered_contracts`,
  `uncovered_contracts`, `uncovered_shares`.
- **`Dashboard.tsx`**: two tabs, "Credit spreads" | "Covered calls", filtering the single
  `listSpreads(false)` result by `spread_type` client-side. Snapshot controls + countdown
  stay above the tabs. Each tab renders its own card grid and empty state.
- **`CoveredCallCard.tsx`** (new): underlying, DTE, P&L (colored), call strike(s), shares,
  coverage badge ("2/2 covered" or "1 uncovered"), premium. Links to `/spread/:id`.
- **`format.ts`**: `formatSpreadType` maps `COVERED_CALL` → "Covered Call".
- **`SpreadDetail.tsx`**: reused; header gets a small conditional block showing shares /
  coverage / premium when `spread_type === "COVERED_CALL"`. `PnLChart` unchanged.

## 7. Testing

- **Detector unit tests** (`test_covered_call_detector.py` or extend existing): fully
  covered (200 shares, 2 short calls → 2 covered, 0 uncovered); partially covered (100
  shares, 2 short calls → 1 covered, 1 uncovered contract); extra shares (250 shares, 1
  short call → 1 covered, 150 uncovered shares); naked call ignored (0 shares, 1 short call
  → no covered call emitted).
- **`moomoo_client` test**: a `US.META` stock row parses into a `RawStock` with correct
  underlying/qty/cost; an option row is not returned by `list_stock_positions`.
- **API e2e** (extend `test_api.py`): fake client returns 200 shares + 2 short calls →
  snapshot → one `COVERED_CALL` spread with correct `pnl_unrealised`, coverage fields, and
  `net_credit`; `/spreads/{id}/history` returns points; a second snapshot with a changed
  stock `position_id` does not duplicate the position (regression parity with the leg fix).

## Out of scope

- Manual covered-call editing in the Groupings page.
- Naked short calls (no backing shares).
- Rolling / multi-expiry call ladders beyond storing the nearest expiry on the Spread.

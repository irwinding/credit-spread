import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api } from "../api/client";
import { LegList } from "../components/LegList";
import { PnLChart } from "../components/PnLChart";
import { daysUntil, fmtMoney, formatSpreadType } from "../lib/format";

export function SpreadDetail() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();

  const { data: spread } = useQuery({
    queryKey: ["spread", id],
    queryFn: () => api.getSpread(id!),
    enabled: !!id,
  });

  const { data: history } = useQuery({
    queryKey: ["spread", id, "history"],
    queryFn: () => api.getHistory(id!),
    enabled: !!id,
  });

  const lock = useMutation({
    mutationFn: (locked: boolean) =>
      api.patchSpread(id!, { user_locked: locked }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["spread", id] }),
  });

  const updateStop = useMutation({
    mutationFn: (stop_loss_pct: number | null) =>
      api.patchSpread(id!, { stop_loss_pct }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["spread", id] }),
  });

  const [stopInput, setStopInput] = useState<string>("");
  useEffect(() => {
    setStopInput(spread?.stop_loss_pct ?? "");
  }, [spread?.stop_loss_pct]);

  if (!spread) {
    return <div className="text-muted">Loading…</div>;
  }

  const latest = history?.points.at(-1);
  const pnlNum = latest ? Number(latest.pnl_unrealised) : null;
  const netCreditNum =
    spread.net_credit != null ? Number(spread.net_credit) : null;

  const submitStop = () => {
    const trimmed = stopInput.trim();
    if (trimmed === "") {
      updateStop.mutate(null);
      return;
    }
    const n = Number(trimmed);
    if (!Number.isFinite(n) || n < 0) return;
    updateStop.mutate(n);
  };

  return (
    <div className="space-y-6">
      <Link to="/" className="text-sm text-muted hover:text-fg">
        ← Dashboard
      </Link>

      <div className="flex items-baseline justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            {spread.underlying}{" "}
            <span className="text-muted text-base">
              {formatSpreadType(spread.spread_type)}
            </span>
            {spread.stop_loss_breached && (
              <span className="ml-3 inline-block px-2 py-0.5 text-xs rounded-md bg-red-900/40 text-red-300 border border-red-700 align-middle">
                STOP LOSS BREACHED
              </span>
            )}
          </h1>
          <p className="text-sm text-muted mt-1">
            {spread.short_strike}/{spread.long_strike} · expires {spread.expiry} (
            {daysUntil(spread.expiry)}d)
          </p>
        </div>
        <div className="text-right">
          <div className="stat">Unrealised PnL</div>
          <div
            className={`text-2xl font-mono ${
              pnlNum == null ? "text-muted" : pnlNum >= 0 ? "pnl-pos" : "pnl-neg"
            }`}
          >
            {pnlNum == null ? "—" : fmtMoney(pnlNum)}
          </div>
        </div>
      </div>

      <div className="panel p-4">
        {history && history.points.length > 0 ? (
          <PnLChart points={history.points} underlying={spread.underlying} />
        ) : (
          <div className="text-muted text-sm py-12 text-center">
            No snapshots yet. Take one from the Dashboard.
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="panel p-4 lg:col-span-2">
          <h2 className="text-sm uppercase tracking-wider text-muted mb-3">
            Legs
          </h2>
          <LegList legs={spread.legs} />
        </div>
        <div className="panel p-4 space-y-3">
          <Field
            label="Net credit (max profit)"
            value={netCreditNum == null ? "—" : fmtMoney(netCreditNum)}
          />
          <Field label="Width" value={spread.width ?? "—"} />
          <Field label="Quantity" value={String(spread.quantity)} />
          <Field label="Detection" value={spread.detection_mode} />

          <div className="pt-2 border-t border-border space-y-1">
            <label className="flex justify-between text-sm items-center gap-2">
              <span className="text-muted">Stop loss (% of credit)</span>
              <input
                type="number"
                min={0}
                step={1}
                value={stopInput}
                onChange={(e) => setStopInput(e.target.value)}
                onBlur={submitStop}
                onKeyDown={(e) => {
                  if (e.key === "Enter") (e.target as HTMLInputElement).blur();
                }}
                placeholder="—"
                className="w-20 font-mono text-right bg-transparent border border-border rounded-md px-2 py-0.5 focus:border-accent focus:outline-none"
              />
            </label>
            {netCreditNum != null && spread.stop_loss_pct != null && (
              <div className="text-[10px] text-muted text-right font-mono">
                triggers at {fmtMoney(
                  -(Number(spread.stop_loss_pct) / 100) * netCreditNum,
                )}
              </div>
            )}
          </div>

          <button
            className="w-full text-sm px-3 py-1.5 rounded-md border border-border hover:border-accent"
            onClick={() => lock.mutate(!spread.user_locked)}
            disabled={lock.isPending}
          >
            {spread.user_locked ? "Unlock grouping" : "Lock grouping"}
          </button>
        </div>
      </div>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between text-sm">
      <span className="text-muted">{label}</span>
      <span className="font-mono">{value}</span>
    </div>
  );
}

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";
import { SnapshotCountdown } from "../components/SnapshotCountdown";
import { SpreadCard } from "../components/SpreadCard";

export function Dashboard() {
  const qc = useQueryClient();
  const { data: spreads, isLoading, error } = useQuery({
    queryKey: ["spreads"],
    queryFn: () => api.listSpreads(false),
  });

  const snap = useMutation({
    mutationFn: () => api.triggerSnapshot(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["spreads"] });
      qc.invalidateQueries({ queryKey: ["snapshotStatus"] });
    },
  });

  return (
    <div>
      <div className="flex items-baseline justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Open spreads</h1>
          <p className="text-sm text-muted mt-1">
            Snapshots run every 5 min during US market hours. Click a card for the PnL chart.
          </p>
        </div>
        <div className="flex items-center gap-4">
          <SnapshotCountdown />
          <button
            className="text-sm px-3 py-1.5 rounded-md border border-border hover:border-accent disabled:opacity-50"
            onClick={() => snap.mutate()}
            disabled={snap.isPending}
          >
            {snap.isPending ? "Snapshotting…" : "Snapshot now"}
          </button>
        </div>
      </div>

      {isLoading && <div className="text-muted">Loading…</div>}
      {error && (
        <div className="panel p-4 pnl-neg text-sm">
          Failed to load: {(error as Error).message}
        </div>
      )}

      {spreads && spreads.length === 0 && (
        <div className="panel p-8 text-center text-muted">
          No open spreads yet. Make sure moomoo OpenD is running, then take a snapshot.
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {spreads?.map((s) => (
          <SpreadCard key={s.id} spread={s} />
        ))}
      </div>
    </div>
  );
}

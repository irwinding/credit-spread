import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { api } from "../api/client";

function formatRemaining(ms: number): string {
  if (ms <= 0) return "0s";
  const totalSec = Math.floor(ms / 1000);
  const h = Math.floor(totalSec / 3600);
  const m = Math.floor((totalSec % 3600) / 60);
  const s = totalSec % 60;
  if (h > 0) return `${h}h ${m}m ${s.toString().padStart(2, "0")}s`;
  if (m > 0) return `${m}m ${s.toString().padStart(2, "0")}s`;
  return `${s}s`;
}

export function SnapshotCountdown() {
  const qc = useQueryClient();
  const { data } = useQuery({
    queryKey: ["snapshotStatus"],
    queryFn: () => api.snapshotStatus(),
    refetchInterval: 60_000,
  });

  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  if (!data) {
    return (
      <div className="text-xs text-muted">
        <span className="stat">Next snapshot</span>
        <div className="font-mono">…</div>
      </div>
    );
  }

  const next = data.next_run_at ? new Date(data.next_run_at).getTime() : null;
  const remaining = next != null ? next - now : null;

  // When the timer crosses zero, refetch status + spreads.
  if (remaining != null && remaining <= 0) {
    queueMicrotask(() => {
      qc.invalidateQueries({ queryKey: ["snapshotStatus"] });
      qc.invalidateQueries({ queryKey: ["spreads"] });
    });
  }

  return (
    <div className="text-right">
      <div className="stat">Next snapshot</div>
      <div
        className="font-mono text-sm tabular-nums"
        title={
          data.next_run_at
            ? `at ${new Date(data.next_run_at).toLocaleString([], {
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              })}`
            : "no scheduled run"
        }
      >
        {remaining != null
          ? remaining > 0
            ? `in ${formatRemaining(remaining)}`
            : "due…"
          : "—"}
      </div>
      {data.last_snapshot_at && (
        <div className="text-[10px] text-muted">
          last{" "}
          {new Date(data.last_snapshot_at).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </div>
      )}
    </div>
  );
}

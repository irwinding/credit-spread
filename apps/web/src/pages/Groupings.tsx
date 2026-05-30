import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../api/client";
import type { Leg } from "../api/types";

export function Groupings() {
  const qc = useQueryClient();
  const { data: legs = [] } = useQuery({
    queryKey: ["legs", "ungrouped"],
    queryFn: () => api.listLegs(true),
  });
  const { data: spreads = [] } = useQuery({
    queryKey: ["spreads", "all"],
    queryFn: () => api.listSpreads(true),
  });

  const [selected, setSelected] = useState<Set<string>>(new Set());

  const create = useMutation({
    mutationFn: (ids: string[]) => api.createSpread(ids),
    onSuccess: () => {
      setSelected(new Set());
      qc.invalidateQueries({ queryKey: ["legs"] });
      qc.invalidateQueries({ queryKey: ["spreads"] });
    },
  });

  const toggle = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  return (
    <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Groupings</h1>
          <p className="text-sm text-muted mt-1">
            Manually pair ungrouped legs into a spread, or lock an existing
            grouping so auto-detect can't change it.
          </p>
        </div>

        <div className="panel p-4">
          <div className="flex items-baseline justify-between mb-3">
            <h2 className="text-sm uppercase tracking-wider text-muted">
              Ungrouped legs ({legs.length})
            </h2>
            <button
              className="text-sm px-3 py-1.5 rounded-md border border-border hover:border-accent disabled:opacity-50"
              onClick={() => create.mutate(Array.from(selected))}
              disabled={selected.size < 2 || create.isPending}
            >
              Group {selected.size > 0 ? `(${selected.size})` : ""}
            </button>
          </div>
          {legs.length === 0 ? (
            <div className="text-sm text-muted">All legs are grouped.</div>
          ) : (
            <ul className="divide-y divide-border">
              {legs.map((l) => (
                <LegRow
                  key={l.id}
                  leg={l}
                  selected={selected.has(l.moomoo_position_id)}
                  onToggle={() => toggle(l.moomoo_position_id)}
                />
              ))}
            </ul>
          )}
        </div>

        <div className="panel p-4">
          <h2 className="text-sm uppercase tracking-wider text-muted mb-3">
            Existing spreads ({spreads.length})
          </h2>
          <ul className="divide-y divide-border text-sm">
            {spreads.map((s) => (
              <li key={s.id} className="py-2 flex justify-between">
                <span>
                  {s.underlying} · {s.spread_type} · {s.short_strike}/
                  {s.long_strike} · {s.expiry}
                </span>
                <span
                  className={`text-xs ${
                    s.user_locked ? "text-accent" : "text-muted"
                  }`}
                >
                  {s.user_locked ? "LOCKED" : s.detection_mode}
                </span>
              </li>
            ))}
          </ul>
        </div>
    </div>
  );
}

function LegRow({
  leg,
  selected,
  onToggle,
}: {
  leg: Leg;
  selected: boolean;
  onToggle: () => void;
}) {
  return (
    <li className="py-2 flex items-center gap-3">
      <input
        type="checkbox"
        checked={selected}
        onChange={onToggle}
        className="accent-accent"
      />
      <span className={`text-xs ${leg.quantity < 0 ? "pnl-neg" : "pnl-pos"}`}>
        {leg.quantity < 0 ? "SHORT" : "LONG"}
      </span>
      <span className="font-mono text-xs flex-1">{leg.option_symbol}</span>
      <span className="font-mono text-xs">qty {leg.quantity}</span>
    </li>
  );
}

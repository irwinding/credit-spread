import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";
import type { Leg, Spread } from "../api/types";
import { GainCard } from "../components/GainCard";
import { OptionCard } from "../components/OptionCard";
import { SnapshotCountdown } from "../components/SnapshotCountdown";
import { SpreadCard } from "../components/SpreadCard";

type DashboardSection = "spreads" | "options" | "gains";

export function Dashboard({ section }: { section: DashboardSection }) {
  const qc = useQueryClient();
  const { data: spreads, isLoading, error } = useQuery({
    queryKey: ["spreads"],
    queryFn: () => api.listSpreads(false),
  });
  const {
    data: allSpreads,
    isLoading: gainsSpreadsLoading,
    error: gainsSpreadsError,
  } = useQuery({
    queryKey: ["spreads", "all"],
    queryFn: () => api.listSpreads(true),
  });
  const {
    data: options,
    isLoading: optionsLoading,
    error: optionsError,
  } = useQuery({
    queryKey: ["legs", "ungrouped"],
    queryFn: () => api.listLegs(true),
  });
  const {
    data: allLegs,
    isLoading: gainsLegsLoading,
    error: gainsLegsError,
  } = useQuery({
    queryKey: ["legs", "all"],
    queryFn: () => api.listLegs(false, true),
  });

  const snap = useMutation({
    mutationFn: () => api.triggerSnapshot(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["spreads"] });
      qc.invalidateQueries({ queryKey: ["legs"] });
      qc.invalidateQueries({ queryKey: ["snapshotStatus"] });
    },
  });
  const gains = buildGains(allSpreads ?? [], allLegs ?? []);
  const sectionMeta = {
    spreads: {
      title: "Vertical spreads",
      description:
        "Open vertical spreads with snapshot PnL. Click a card for the chart.",
    },
    options: {
      title: "Other options",
      description:
        "Ungrouped option positions with the same mark-to-market PnL tracking.",
    },
    gains: {
      title: "Gains",
      description:
        "Closed spreads, options, and strategy outcomes consolidated by Snapshot now.",
    },
  }[section];
  const pageLoading =
    section === "spreads"
      ? isLoading
      : section === "options"
        ? optionsLoading
        : gainsSpreadsLoading || gainsLegsLoading;
  const pageError =
    section === "spreads"
      ? error
      : section === "options"
        ? optionsError
        : gainsSpreadsError ?? gainsLegsError;

  return (
    <>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-baseline sm:justify-between mb-6">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">
              {sectionMeta.title}
            </h1>
            <p className="text-sm text-muted mt-1">{sectionMeta.description}</p>
          </div>
          <div className="flex items-center gap-4">
            <SnapshotCountdown />
            <button
              className="text-sm px-3 py-1.5 rounded-md border border-border hover:border-accent disabled:opacity-50"
              onClick={() => snap.mutate()}
              disabled={snap.isPending}
            >
              {snap.isPending ? "Snapshotting..." : "Snapshot now"}
            </button>
          </div>
        </div>

      {pageLoading && <div className="text-muted">Loading…</div>}
      {pageError && (
        <div className="panel p-4 pnl-neg text-sm">
          Failed to load: {(pageError as Error).message}
        </div>
      )}

      {section === "spreads" && spreads && spreads.length === 0 && (
        <div className="panel p-8 text-center text-muted">
          No open spreads yet. Make sure moomoo OpenD is running, then take a snapshot.
        </div>
      )}
      {section === "options" && options && options.length === 0 && (
        <div className="panel p-8 text-center text-muted">
          No ungrouped options. Take a snapshot to populate open option positions.
        </div>
      )}
      {section === "gains" && gains.length === 0 && (
        <div className="panel p-8 text-center text-muted">
          No closed gains yet. Expired positions are moved here by Snapshot now.
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {section === "spreads" &&
          spreads?.map((s) => <SpreadCard key={s.id} spread={s} />)}
        {section === "options" &&
          options?.map((l) => <OptionCard key={l.id} leg={l} />)}
        {section === "gains" &&
          gains.map((item) => (
            <GainCard
              key={item.kind === "spread" ? `spread-${item.spread.id}` : `leg-${item.leg.id}`}
              item={item}
            />
          ))}
      </div>
    </>
  );
}

function buildGains(spreads: Spread[], legs: Leg[]) {
  const closedSpreads = spreads
    .filter((s) => s.closed_at != null)
    .map((spread) => ({ kind: "spread" as const, spread }));
  const closedStandaloneOptions = legs
    .filter((l) => l.closed_at != null && l.spread_id == null)
    .map((leg) => ({ kind: "option" as const, leg }));

  return [...closedSpreads, ...closedStandaloneOptions].sort((a, b) => {
    const aClosed =
      a.kind === "spread" ? a.spread.closed_at ?? "" : a.leg.closed_at ?? "";
    const bClosed =
      b.kind === "spread" ? b.spread.closed_at ?? "" : b.leg.closed_at ?? "";
    return bClosed.localeCompare(aClosed);
  });
}

import type {
  Leg,
  LegHistory,
  SnapshotResult,
  SnapshotStatus,
  Spread,
  SpreadHistory,
} from "./types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8001";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  listSpreads: (includeClosed = false) =>
    request<Spread[]>(`/spreads?include_closed=${includeClosed}`),
  getSpread: (id: string) => request<Spread>(`/spreads/${id}`),
  getHistory: (id: string) => request<SpreadHistory>(`/spreads/${id}/history`),

  listLegs: (ungroupedOnly = false, includeClosed = false) =>
    request<Leg[]>(
      `/legs?ungrouped_only=${ungroupedOnly}&include_closed=${includeClosed}`,
    ),
  getLegHistory: (id: number) => request<LegHistory>(`/legs/${id}/history`),

  createSpread: (legPositionIds: string[]) =>
    request<Spread>(`/spreads`, {
      method: "POST",
      body: JSON.stringify({ leg_position_ids: legPositionIds }),
    }),

  patchSpread: (
    id: string,
    payload: {
      leg_position_ids?: string[];
      user_locked?: boolean;
      stop_loss_pct?: number | null;
    },
  ) =>
    request<Spread>(`/spreads/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  triggerSnapshot: () =>
    request<SnapshotResult>(`/snapshot/run`, { method: "POST" }),

  snapshotStatus: () => request<SnapshotStatus>(`/snapshot/status`),
};

export function fmtMoney(n: number): string {
  const sign = n < 0 ? "-" : n > 0 ? "+" : "";
  const abs = Math.abs(n);
  return `${sign}$${abs.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

export function formatSpreadType(t: string): string {
  switch (t) {
    case "BULL_PUT":
      return "Bull Put";
    case "BEAR_CALL":
      return "Bear Call";
    default:
      return "Other";
  }
}

export function formatCloseReason(reason: string | null): string {
  switch (reason) {
    case "HELD_TO_EXPIRY":
      return "Held to expiry";
    default:
      return reason ?? "Closed";
  }
}

export function daysUntil(dateIso: string): number {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const target = new Date(dateIso);
  target.setHours(0, 0, 0, 0);
  return Math.round((target.getTime() - today.getTime()) / 86_400_000);
}

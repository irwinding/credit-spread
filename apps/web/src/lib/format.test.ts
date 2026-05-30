import { describe, expect, it } from "vitest";

import { daysUntil, fmtMoney, formatCloseReason, formatSpreadType } from "./format";

describe("fmtMoney", () => {
  it("formats positive values with a leading +", () => {
    expect(fmtMoney(123.45)).toBe("+$123.45");
  });
  it("formats negative values with a -", () => {
    expect(fmtMoney(-50)).toBe("-$50.00");
  });
  it("formats zero without a sign", () => {
    expect(fmtMoney(0)).toBe("$0.00");
  });
});

describe("formatCloseReason", () => {
  it("humanises held-to-expiry closures", () => {
    expect(formatCloseReason("HELD_TO_EXPIRY")).toBe("Held to expiry");
  });
});

describe("formatSpreadType", () => {
  it("humanises spread types", () => {
    expect(formatSpreadType("BULL_PUT")).toBe("Bull Put");
    expect(formatSpreadType("BEAR_CALL")).toBe("Bear Call");
    expect(formatSpreadType("OTHER")).toBe("Other");
  });
});

describe("daysUntil", () => {
  it("returns 0 for today", () => {
    const today = new Date().toISOString().slice(0, 10);
    expect(daysUntil(today)).toBe(0);
  });
});

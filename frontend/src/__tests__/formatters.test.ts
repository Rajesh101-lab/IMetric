import { describe, it, expect } from "vitest";
import {
  formatCompactNumber,
  formatPercent,
  formatRelativeTime,
  formatNumberWithCommas,
} from "../lib/format";

describe("Frontend Formatters", () => {
  it("formats compact numbers accurately", () => {
    expect(formatCompactNumber(null)).toBe("—");
    expect(formatCompactNumber(0)).toBe("0");
    expect(formatCompactNumber(950)).toBe("950");
    expect(formatCompactNumber(12400)).toBe("12.4K");
    expect(formatCompactNumber(1500000)).toBe("1.5M");
    expect(formatCompactNumber(2500000000)).toBe("2.5B");
  });

  it("formats percentages with 2 decimals", () => {
    expect(formatPercent(null)).toBe("—");
    expect(formatPercent(0)).toBe("0.00%");
    expect(formatPercent(0.05423)).toBe("5.42%");
    expect(formatPercent(0.12)).toBe("12.00%");
  });

  it("formats numbers with commas", () => {
    expect(formatNumberWithCommas(null)).toBe("—");
    expect(formatNumberWithCommas(12450)).toBe("12,450");
  });

  it("formats relative time strings", () => {
    expect(formatRelativeTime(null)).toBe("Never");
    const nowIso = new Date().toISOString();
    expect(formatRelativeTime(nowIso)).toBe("Just now");
  });
});

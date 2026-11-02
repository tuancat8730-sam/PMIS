import { describe, expect, it } from "vitest";

import {
  COMMAND_CENTER_PATH,
  fetchCommandCenter,
  filterByProject,
  formatBillionVnd,
  type CommandCenterData,
} from "./command-center";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const SAMPLE: CommandCenterData = {
  as_of: "2026-11-01",
  kpi: {
    contract_value_by_kind: { MAIN: "111070000000.00", CONSULTING: "1120000000.00" },
    contract_value_total: "112190000000.00",
    running_project_count: 2,
    beneficiary_unit_count: 10,
    pending_signature_count: null,
    red_alert_count: 2,
  },
  projects: [
    { id: "1", code: "CC-A", short_name: "A", health: "AT_RISK", red_alert_count: 1, max_slippage_days: 3 },
    { id: "2", code: "CC-B", short_name: "B", health: "CRITICAL", red_alert_count: 1, max_slippage_days: 9 },
  ],
  red_alerts: [
    { project_code: "CC-A", source: "MILESTONE", code: "M1", title: "Mốc 1", due_date: "2026-11-02" },
    { project_code: "CC-B", source: "RISK", code: "R1", title: "Rủi ro 1", due_date: "2026-10-30" },
  ],
  contract_countdowns: [
    {
      project_code: "CC-B",
      contract_number: "29/HĐKT",
      status: "WARNING",
      expiration_date: "2026-11-20",
      days_remaining: 19,
    },
  ],
};

describe("fetchCommandCenter", () => {
  it("calls the endpoint with a bearer token and no cache", async () => {
    // Arrange
    const calls: { url: string; init: RequestInit | undefined }[] = [];
    const fakeFetch = async (url: string | URL | Request, init?: RequestInit) => {
      calls.push({ url: String(url), init });
      return jsonResponse(SAMPLE);
    };

    // Act
    await fetchCommandCenter("token-123", fakeFetch, "http://api.test");

    // Assert
    expect(calls[0]?.url).toBe(`http://api.test${COMMAND_CENTER_PATH}`);
    expect(calls[0]?.init?.headers).toEqual({ Authorization: "Bearer token-123" });
    expect(calls[0]?.init?.cache).toBe("no-store");
  });

  it("throws with the status code when the API rejects the request", async () => {
    // Arrange
    const fakeFetch = async () => jsonResponse({ detail: "no" }, 401);

    // Act / Assert
    await expect(fetchCommandCenter("bad", fakeFetch, "http://api.test")).rejects.toThrow("401");
  });

  it("rejects a body that is not the command center shape", async () => {
    // Arrange
    const fakeFetch = async () => jsonResponse({ projects: "không phải mảng" });

    // Act / Assert
    await expect(fetchCommandCenter("token", fakeFetch, "http://api.test")).rejects.toThrow(
      "không hợp lệ",
    );
  });
});

describe("filterByProject", () => {
  it("returns all rows when no project is selected", () => {
    // Act
    const filtered = filterByProject(SAMPLE, null);

    // Assert
    expect(filtered.red_alerts).toHaveLength(2);
    expect(filtered.projects).toHaveLength(2);
  });

  it("keeps only the selected project's alerts, countdowns and health row", () => {
    // Act
    const filtered = filterByProject(SAMPLE, "CC-B");

    // Assert
    expect(filtered.red_alerts.map((row) => row.code)).toEqual(["R1"]);
    expect(filtered.contract_countdowns).toHaveLength(1);
    expect(filtered.projects.map((row) => row.code)).toEqual(["CC-B"]);
  });
});

describe("formatBillionVnd", () => {
  it("formats an amount in billions with Vietnamese decimal separator", () => {
    // Act
    const text = formatBillionVnd("111070000000.00");

    // Assert
    expect(text).toContain("111,07");
    expect(text).toContain("tỷ");
  });
});

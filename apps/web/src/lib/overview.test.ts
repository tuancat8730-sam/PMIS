import { describe, expect, it, vi } from "vitest";

import {
  decisionKindLabel,
  fetchProjectOverview,
  formatVnd,
  type ContractSummaryRow,
  type LegalDecisionRow,
  type ProjectSummary,
} from "./overview";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const PROJECT: ProjectSummary = {
  id: "p1",
  code: "SGD-HCM-CSVC-2026",
  name: "Xây dựng hệ thống quản lý dữ liệu về cơ sở vật chất",
  investor_name: "Sở GD&ĐT TP.HCM",
  decision_authority: "UBND TP.HCM",
  total_investment: "5999498939.00",
  start_date: null,
  end_date: null,
};

const DECISION: LegalDecisionRow = {
  id: "d1",
  kind: "PROJECT_APPROVAL",
  decision_no: "1595/QĐ-SGDĐT",
  decision_date: "2026-05-22",
  issuing_authority: "Sở GD&ĐT TP.HCM",
  amount: "5999498939.00",
  funding_source: "Ngân sách Nhà nước",
  execution_period: "2026 - 2027",
  note: null,
};

const CONTRACT: ContractSummaryRow = {
  id: "c1",
  package_name: "Gói triển khai",
  package_kind: "IMPLEMENTATION",
  contract_number: "29/HĐKT-DVN",
  signed_date: "2026-09-21",
  expiration_date: null,
  contract_value: "4848186000.00",
};

function routeByPath(path: string): Response {
  if (path.endsWith("/contracts")) return jsonResponse([CONTRACT]);
  if (path.endsWith("/legal-decisions")) return jsonResponse([DECISION]);
  return jsonResponse(PROJECT);
}

describe("fetchProjectOverview", () => {
  it("loads project, decisions and contracts with the bearer token", async () => {
    // Arrange
    const fetchImpl = vi.fn(async (url: RequestInfo | URL) => routeByPath(String(url)));

    // Act
    const overview = await fetchProjectOverview("p1", "token-abc", fetchImpl, "http://api.test");

    // Assert
    expect(overview).toEqual({ project: PROJECT, decisions: [DECISION], contracts: [CONTRACT] });
    const urls = fetchImpl.mock.calls.map((call) => call[0]);
    expect(urls).toEqual(
      expect.arrayContaining([
        "http://api.test/api/v1/projects/p1",
        "http://api.test/api/v1/projects/p1/legal-decisions",
        "http://api.test/api/v1/projects/p1/contracts",
      ]),
    );
  });

  it("throws with the HTTP status when any request fails", async () => {
    // Arrange
    const fetchImpl = vi.fn(async (url: RequestInfo | URL) =>
      String(url).endsWith("/contracts")
        ? jsonResponse({ detail: "x" }, 403)
        : routeByPath(String(url)),
    );

    // Act
    const load = fetchProjectOverview("p1", "token", fetchImpl, "http://api.test");

    // Assert
    await expect(load).rejects.toThrow("mã 403");
  });
});

describe("formatVnd", () => {
  it("formats the amount with vi-VN grouping and the đồng suffix", () => {
    // Act
    const text = formatVnd("5999498939.00");

    // Assert
    expect(text).toBe("5.999.498.939 đ");
  });
});

describe("decisionKindLabel", () => {
  it("returns the Vietnamese label for a decision kind", () => {
    // Act
    const label = decisionKindLabel("PROJECT_APPROVAL");

    // Assert
    expect(label).toBe("Quyết định phê duyệt dự án");
  });
});

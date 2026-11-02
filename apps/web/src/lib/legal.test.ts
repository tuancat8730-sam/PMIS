import { describe, expect, it, vi } from "vitest";

import {
  fetchLegalDocuments,
  groupLegalDocumentsByPhase,
  legalPhaseLabel,
  legalStatusLabel,
  type LegalDocumentRow,
} from "./legal";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function makeDocument(overrides: Partial<LegalDocumentRow>): LegalDocumentRow {
  return {
    id: "d1",
    project_id: "p1",
    stt: 1,
    phase_group: "PREPARATION",
    doc_code_symbol: null,
    doc_name: "QĐ phê duyệt dự toán",
    issuing_authority: "Sở GD&ĐT",
    issue_date: "2025-08-20",
    is_mandatory: true,
    maturity_status: "MISSING",
    pm_action_required: null,
    assigned_to: null,
    due_date: null,
    notes: null,
    ...overrides,
  };
}

describe("fetchLegalDocuments", () => {
  it("sends the bearer token and returns the document list", async () => {
    // Arrange
    const documents = [makeDocument({ stt: 1 })];
    const fetchImpl = vi.fn(async () => jsonResponse(documents));

    // Act
    const result = await fetchLegalDocuments("p1", "token-abc", fetchImpl, "http://api.test");

    // Assert
    expect(result).toEqual(documents);
    const [url, init] = fetchImpl.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("http://api.test/api/v1/projects/p1/legal-documents");
    expect(init.headers).toEqual({ Authorization: "Bearer token-abc" });
  });

  it("throws with the HTTP status when the request fails", async () => {
    // Arrange
    const fetchImpl = vi.fn(async () => jsonResponse({ detail: "x" }, 403));

    // Act and Assert
    await expect(
      fetchLegalDocuments("p1", "token-abc", fetchImpl, "http://api.test"),
    ).rejects.toThrow("mã 403");
  });

  it("rejects a payload that is not a list", async () => {
    // Arrange
    const fetchImpl = vi.fn(async () => jsonResponse({ total: 1 }));

    // Act and Assert
    await expect(
      fetchLegalDocuments("p1", "token-abc", fetchImpl, "http://api.test"),
    ).rejects.toThrow("không hợp lệ");
  });
});

describe("groupLegalDocumentsByPhase", () => {
  it("orders groups by phase and keeps stt order inside each group", () => {
    // Arrange
    const documents = [
      makeDocument({ id: "a", stt: 30, phase_group: "ACCEPTANCE" }),
      makeDocument({ id: "b", stt: 2, phase_group: "PREPARATION" }),
      makeDocument({ id: "c", stt: 1, phase_group: "PREPARATION" }),
    ];

    // Act
    const groups = groupLegalDocumentsByPhase(documents);

    // Assert
    expect(groups.map((group) => group.phase)).toEqual(["PREPARATION", "ACCEPTANCE"]);
    expect(groups[0].rows.map((row) => row.id)).toEqual(["c", "b"]);
  });

  it("omits phases that have no documents", () => {
    // Act
    const groups = groupLegalDocumentsByPhase([makeDocument({ phase_group: "BIDDING" })]);

    // Assert
    expect(groups).toHaveLength(1);
    expect(groups[0].phase).toBe("BIDDING");
  });

  it("does not mutate the input array", () => {
    // Arrange
    const documents = [makeDocument({ stt: 2 }), makeDocument({ id: "d2", stt: 1 })];
    const snapshot = documents.map((document) => document.stt);

    // Act
    groupLegalDocumentsByPhase(documents);

    // Assert
    expect(documents.map((document) => document.stt)).toEqual(snapshot);
  });
});

describe("Vietnamese labels", () => {
  it("returns the Vietnamese label for each maturity status", () => {
    // Assert
    expect(legalStatusLabel("MISSING")).toBe("Chưa có file");
    expect(legalStatusLabel("DISCREPANCY_FOUND")).toBe("Có sai sót");
    expect(legalStatusLabel("SIGNED_SCAN_PDF")).toBe("Đã ký (bản scan)");
  });

  it("returns the Vietnamese label for each phase group", () => {
    // Assert
    expect(legalPhaseLabel("PREPARATION")).toBe("Chuẩn bị đầu tư");
    expect(legalPhaseLabel("ACCEPTANCE")).toBe("Nghiệm thu, thanh lý");
  });
});

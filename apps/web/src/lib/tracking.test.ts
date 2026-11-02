import { describe, expect, it, vi } from "vitest";

import {
  fetchRiskMatrix,
  fetchScheduleMatrix,
  formatDateVi,
  riskLevelLabel,
  type RiskMatrixData,
  type ScheduleMatrixData,
} from "./tracking";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const SCHEDULE: ScheduleMatrixData = {
  total: 1,
  rows: [
    {
      id: "m1",
      project_id: "p1",
      code: "M1",
      name: "Giao hàng đợt 1",
      baseline_start: null,
      baseline_end: "2026-11-10",
      adjusted_start: null,
      adjusted_end: null,
      actual_end: null,
      is_hard_deadline: true,
      progress_percent: "40.00",
      status: "IN_PROGRESS",
      display_status: "AT_RISK",
      slippage_days: 0,
      responsible_party: "Liên danh",
      evidence_summary: null,
      deliverables: "Biên bản 60 đơn vị",
      acceptance_conditions: null,
      tvgs_checkpoint: "W1",
      pm_comment: null,
    },
  ],
};

const RISKS: RiskMatrixData = {
  total: 1,
  rows: [
    {
      id: "r1",
      code: "R1",
      record_type: "RISK",
      title: "Dữ liệu nguồn chậm",
      status: "OPEN",
      owner: null,
      due_date: null,
      impact: "VERY_HIGH",
      likelihood: "HIGH",
      score: 12,
      coordinating_units: "Sở GDĐT",
    },
  ],
};

describe("fetchScheduleMatrix", () => {
  it("gọi đúng đường dẫn có Bearer token và trả về dữ liệu", async () => {
    // Arrange
    const fetchImpl = vi.fn(async () => jsonResponse(SCHEDULE));

    // Act
    const data = await fetchScheduleMatrix("p1", "token-abc", fetchImpl, "http://api.test");

    // Assert
    expect(fetchImpl).toHaveBeenCalledWith(
      "http://api.test/api/v1/projects/p1/schedule-matrix",
      expect.objectContaining({ headers: { Authorization: "Bearer token-abc" } }),
    );
    expect(data.rows[0].code).toBe("M1");
  });

  it("báo lỗi khi API trả về mã không thành công", async () => {
    // Arrange
    const fetchImpl = vi.fn(async () => jsonResponse({}, 403));

    // Act / Assert
    await expect(
      fetchScheduleMatrix("p1", "token-abc", fetchImpl, "http://api.test"),
    ).rejects.toThrow("mã 403");
  });

  it("từ chối dữ liệu không đúng biên", async () => {
    // Arrange
    const fetchImpl = vi.fn(async () => jsonResponse({ rows: "sai" }));

    // Act / Assert
    await expect(
      fetchScheduleMatrix("p1", "token-abc", fetchImpl, "http://api.test"),
    ).rejects.toThrow("không hợp lệ");
  });
});

describe("fetchRiskMatrix", () => {
  it("gọi đúng đường dẫn risk-matrix và trả về dữ liệu", async () => {
    // Arrange
    const fetchImpl = vi.fn(async () => jsonResponse(RISKS));

    // Act
    const data = await fetchRiskMatrix("p1", "token-abc", fetchImpl, "http://api.test");

    // Assert
    expect(fetchImpl).toHaveBeenCalledWith(
      "http://api.test/api/v1/projects/p1/risk-matrix",
      expect.anything(),
    );
    expect(data.rows[0].score).toBe(12);
  });
});

describe("riskLevelLabel", () => {
  it("đổi mức rủi ro sang tiếng Việt và xử lý giá trị trống", () => {
    // Arrange / Act / Assert
    expect(riskLevelLabel("VERY_HIGH")).toBe("Rất cao");
    expect(riskLevelLabel("LOW")).toBe("Thấp");
    expect(riskLevelLabel(null)).toBe("Chưa đánh giá");
  });
});

describe("formatDateVi", () => {
  it("định dạng ngày ISO theo dd/mm/yyyy", () => {
    // Arrange / Act / Assert
    expect(formatDateVi("2026-11-10")).toBe("10/11/2026");
    expect(formatDateVi(null)).toBe("—");
  });
});

import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { RiskTable } from "./risk-table";
import { ScheduleTable } from "./schedule-table";
import type { RiskRow, ScheduleRow } from "../../lib/tracking";

const MILESTONE: ScheduleRow = {
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
  slippage_days: 2,
  responsible_party: "Liên danh",
  evidence_summary: null,
  deliverables: "Biên bản 60 đơn vị",
  acceptance_conditions: "CO, CQ đủ",
  tvgs_checkpoint: "W1 kiểm tra kho",
  pm_comment: "Chờ serial",
};

const RISK: RiskRow = {
  id: "r1",
  code: "R1",
  record_type: "RISK",
  title: "Dữ liệu nguồn chậm",
  status: "OPEN",
  owner: "QLDA",
  due_date: "2026-11-20",
  impact: "VERY_HIGH",
  likelihood: null,
  score: null,
  coordinating_units: "Sở GDĐT; TVGS",
};

describe("ScheduleTable", () => {
  it("hiển thị mốc với nhãn trạng thái tiếng Việt và các cột theo dõi", () => {
    // Arrange / Act
    const html = renderToStaticMarkup(<ScheduleTable rows={[MILESTONE]} />);

    // Assert
    expect(html).toContain("M1");
    expect(html).toContain("10/11/2026");
    expect(html).toContain("Có nguy cơ");
    expect(html).toContain("Biên bản 60 đơn vị");
    expect(html).toContain("Chờ serial");
  });

  it("hiển thị thông báo khi không có mốc nào", () => {
    // Arrange / Act
    const html = renderToStaticMarkup(<ScheduleTable rows={[]} />);

    // Assert
    expect(html).toContain("Chưa có mốc tiến độ");
  });
});

describe("RiskTable", () => {
  it("hiển thị mức tác động, khả năng chưa đánh giá và đơn vị phối hợp", () => {
    // Arrange / Act
    const html = renderToStaticMarkup(<RiskTable rows={[RISK]} />);

    // Assert
    expect(html).toContain("Rất cao");
    expect(html).toContain("Chưa đánh giá");
    expect(html).toContain("Sở GDĐT; TVGS");
    expect(html).toContain("—");
  });

  it("hiển thị thông báo khi không có rủi ro nào", () => {
    // Arrange / Act
    const html = renderToStaticMarkup(<RiskTable rows={[]} />);

    // Assert
    expect(html).toContain("Chưa có rủi ro");
  });
});

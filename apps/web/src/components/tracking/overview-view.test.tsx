import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { OverviewView } from "./overview-view";
import type { ProjectOverview } from "../../lib/overview";

const OVERVIEW: ProjectOverview = {
  project: {
    id: "p1",
    code: "SGD-HCM-CSVC-2026",
    name: "Xây dựng hệ thống quản lý dữ liệu về cơ sở vật chất",
    investor_name: "Sở GD&ĐT TP.HCM",
    decision_authority: "UBND TP.HCM",
    total_investment: "5999498939.00",
    start_date: null,
    end_date: null,
  },
  decisions: [
    {
      id: "d1",
      kind: "PROJECT_APPROVAL",
      decision_no: "1595/QĐ-SGDĐT",
      decision_date: "2026-05-22",
      issuing_authority: "Sở GD&ĐT TP.HCM",
      amount: "5999498939.00",
      funding_source: "Ngân sách Nhà nước",
      execution_period: "2026 - 2027",
      note: null,
    },
  ],
  contracts: [
    {
      id: "c1",
      package_name: "Gói triển khai",
      package_kind: "IMPLEMENTATION",
      contract_number: "29/HĐKT-DVN",
      signed_date: "2026-09-21",
      expiration_date: null,
      contract_value: "4848186000.00",
    },
  ],
};

describe("OverviewView", () => {
  it("shows the total investment, funding source and execution period", () => {
    // Act
    const markup = renderToStaticMarkup(<OverviewView overview={OVERVIEW} />);

    // Assert
    expect(markup).toContain("5.999.498.939 đ");
    expect(markup).toContain("Ngân sách Nhà nước");
    expect(markup).toContain("2026 - 2027");
  });});

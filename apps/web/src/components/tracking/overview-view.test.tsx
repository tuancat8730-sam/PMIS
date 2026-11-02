import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { OverviewView } from "./overview-view";
import type { ProjectOverview } from "../../lib/overview";
import type { OverviewSections } from "../../lib/overview-sections";

const OVERVIEW: ProjectOverview = {
  project: {
    id: "p1",
    code: "SGD-HCM-CSVC-2026",
    name: "Xây dựng hệ thống quản lý dữ liệu về cơ sở vật chất",
    investor_name: "Sở GD&ĐT TP.HCM",
    decision_authority: "Ủy ban nhân dân Thành phố Hồ Chí Minh",
    legal_representative: "Ông Nguyễn Văn Hiếu — Giám đốc Sở GD&ĐT",
    qlda_form: "Chủ đầu tư thuê tư vấn quản lý dự án (Công ty Sài Gòn Mới)",
    disbursement_deadline: "09/12/2026 (Hạn chót giải ngân năm 2026)",
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
      package_name: "Gói TVGS",
      package_kind: "CONSULTING",
      contract_number: "24.8.26/HĐTV/SGDĐT-CRYSTAL",
      signed_date: "2026-08-24",
      expiration_date: "2027-01-21",
      contract_value: "120000000.00",
      contractor_name: null,
      role_label: "Tư vấn giám sát",
      contact_person: null,
      status_note: null,
    },
  ],
};

const SECTIONS: OverviewSections = {
  budgetItems: [
    {
      id: "b1",
      project_id: "p1",
      category: "SOFTWARE",
      label: "Chi phí phần mềm",
      amount: "5447400000.00",
      note: "Giá trúng HĐ trên khai 4.848.186.000 đ",
      sort_order: 1,
    },
  ],
  requirements: [],
};

const MISSING_TEXT = "Chưa có nguồn";

describe("OverviewView section I", () => {
  it("shows the decision authority, total investment, funding source and period", () => {
    // Act
    const markup = renderToStaticMarkup(<OverviewView overview={OVERVIEW} sections={SECTIONS} />);

    // Assert
    expect(markup).toContain("Ủy ban nhân dân Thành phố Hồ Chí Minh");
    expect(markup).toContain("5.999.498.939 đ");
    expect(markup).toContain("Ngân sách Nhà nước");
    expect(markup).toContain("2026 - 2027");
  });

  it("shows legal representative, QLDA form and disbursement deadline", () => {
    // Act
    const markup = renderToStaticMarkup(<OverviewView overview={OVERVIEW} sections={SECTIONS} />);

    // Assert
    expect(markup).toContain("Ông Nguyễn Văn Hiếu — Giám đốc Sở GD&amp;ĐT");
    expect(markup).toContain("Chủ đầu tư thuê tư vấn quản lý dự án (Công ty Sài Gòn Mới)");
    expect(markup).toContain("09/12/2026 (Hạn chót giải ngân năm 2026)");
  });

  it("shows approval decisions with number and date in dd/mm/yyyy", () => {
    // Act
    const markup = renderToStaticMarkup(<OverviewView overview={OVERVIEW} sections={SECTIONS} />);

    // Assert
    expect(markup).toContain("1595/QĐ-SGDĐT, ngày 22/05/2026");
  });

  it("shows each budget item with its amount and note", () => {
    // Act
    const markup = renderToStaticMarkup(<OverviewView overview={OVERVIEW} sections={SECTIONS} />);

    // Assert
    expect(markup).toContain("Chi phí phần mềm");
    expect(markup).toContain("5.447.400.000 đ");
    expect(markup).toContain("Giá trúng HĐ trên khai 4.848.186.000 đ");
  });

  it("marks fields the data does not have as missing instead of guessing", () => {
    // Act
    const markup = renderToStaticMarkup(<OverviewView overview={OVERVIEW} sections={SECTIONS} />);

    // Assert
    expect(markup).toContain(MISSING_TEXT);
  });
});

describe("OverviewView section II", () => {
  it("shows the project owner as its own row before the contracts", () => {
    // Act
    const markup = renderToStaticMarkup(<OverviewView overview={OVERVIEW} sections={SECTIONS} />);

    // Assert
    expect(markup).toContain("Chủ đầu tư (CĐT)");
    expect(markup.indexOf("Chủ đầu tư (CĐT)")).toBeLessThan(markup.indexOf("Tư vấn giám sát"));
  });

  it("shows contract role, number, dates and value", () => {
    // Act
    const markup = renderToStaticMarkup(<OverviewView overview={OVERVIEW} sections={SECTIONS} />);

    // Assert
    expect(markup).toContain("Tư vấn giám sát");
    expect(markup).toContain("24.8.26/HĐTV/SGDĐT-CRYSTAL");
    expect(markup).toContain("24/08/2026");
    expect(markup).toContain("21/01/2027");
    expect(markup).toContain("120.000.000 đ");
  });
});

describe("OverviewView section III", () => {
  it("shows a missing-source message when no technical requirement is loaded", () => {
    // Act
    const markup = renderToStaticMarkup(<OverviewView overview={OVERVIEW} sections={SECTIONS} />);

    // Assert
    expect(markup).toContain("III. Quy mô kỹ thuật và chỉ tiêu nghiệm thu ràng buộc");
    expect(markup).toContain("Chưa có nguồn cho mục III");
  });

  it("shows each technical requirement with its acceptance criteria", () => {
    // Arrange
    const sections: OverviewSections = {
      budgetItems: [],
      requirements: [
        {
          id: "r1",
          project_id: "p1",
          sort_order: 1,
          item: "Hiệu năng phản hồi",
          standard: "Phản hồi trung bình < 2 giây",
          legal_basis: null,
          solution: null,
          responsibility: "LD DVN (DTH)",
          acceptance_criteria: "Báo cáo kiểm thử tải",
          related_risk: null,
          monitoring_status: "Chờ test UAT",
        },
      ],
    };

    // Act
    const markup = renderToStaticMarkup(<OverviewView overview={OVERVIEW} sections={sections} />);

    // Assert
    expect(markup).toContain("Hiệu năng phản hồi");
    expect(markup).toContain("Báo cáo kiểm thử tải");
    expect(markup).toContain("Chờ test UAT");
  });
});

import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { DecisionsView } from "./decisions-view";
import type { LegalDecisionRow } from "../../lib/overview";

const APPROVAL: LegalDecisionRow = {
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

describe("DecisionsView", () => {
  it("shows the kind heading, decision number and date", () => {
    // Act
    const markup = renderToStaticMarkup(<DecisionsView decisions={[APPROVAL]} />);

    // Assert
    expect(markup).toContain("Quyết định phê duyệt dự án");
    expect(markup).toContain("1595/QĐ-SGDĐT");
    expect(markup).toContain("22/05/2026");
  });

  it("shows the amount formatted in vi-VN", () => {
    // Act
    const markup = renderToStaticMarkup(<DecisionsView decisions={[APPROVAL]} />);

    // Assert
    expect(markup).toContain("5.999.498.939 đ");
  });

  it("shows an empty message when there are no decisions", () => {
    // Act
    const markup = renderToStaticMarkup(<DecisionsView decisions={[]} />);

    // Assert
    expect(markup).toContain("Chưa có quyết định nào");
  });
});

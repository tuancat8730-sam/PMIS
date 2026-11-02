import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { LegalTable } from "./legal-table";
import type { LegalDocumentRow } from "../../lib/legal";

const DOCUMENT: LegalDocumentRow = {
  id: "d1",
  project_id: "p1",
  stt: 29,
  phase_group: "ACCEPTANCE",
  doc_code_symbol: "015-2026/BBNT/SGDHCM-SGM",
  doc_name: "BB nghiệm thu và thanh lý HĐ",
  issuing_authority: "Sở GD&ĐT - Cty Sài Gòn Mới",
  issue_date: "2026-06-19",
  is_mandatory: true,
  maturity_status: "SIGNED_SCAN_PDF",
  pm_action_required: null,
  assigned_to: null,
  due_date: null,
  notes: null,
};

describe("LegalTable", () => {
  it("renders each phase heading with its Vietnamese label", () => {
    // Act
    const markup = renderToStaticMarkup(<LegalTable rows={[DOCUMENT]} />);

    // Assert
    expect(markup).toContain("Nghiệm thu, thanh lý");
  });

  it("renders the document name, issue date and status label", () => {
    // Act
    const markup = renderToStaticMarkup(<LegalTable rows={[DOCUMENT]} />);

    // Assert
    expect(markup).toContain("BB nghiệm thu và thanh lý HĐ");
    expect(markup).toContain("19/06/2026");
    expect(markup).toContain("Đã ký (bản scan)");
  });

  it("shows an empty-state message when there are no documents", () => {
    // Act
    const markup = renderToStaticMarkup(<LegalTable rows={[]} />);

    // Assert
    expect(markup).toContain("Chưa có hồ sơ pháp lý nào.");
  });
});

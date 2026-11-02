import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { FileRegisterTable } from "./file-register-table";
import type { FileRegisterRow } from "../../lib/file-register";

const ENTRY: FileRegisterRow = {
  id: "f1",
  project_id: "p1",
  stt: 4,
  folder_path: "Tài liệu lưu trữ / 2.Thủ tục",
  file_name: "1595_QD phe duyet du an...signed.pdf",
  file_format: "PDF Signed",
  storage_location: "Google Drive",
  purpose: "Quyết định phê duyệt dự án",
  legal_status: "Bản scan ký chính thức",
  security_ownership: "Pháp lý CĐT",
  next_action: "Căn cứ pháp lý nghiệm thu gốc",
  drive_file_id: null,
};

describe("FileRegisterTable", () => {
  it("renders the file name, format and next action of each entry", () => {
    // Act
    const markup = renderToStaticMarkup(<FileRegisterTable rows={[ENTRY]} />);

    // Assert
    expect(markup).toContain("1595_QD phe duyet du an...signed.pdf");
    expect(markup).toContain("PDF Signed");
    expect(markup).toContain("Căn cứ pháp lý nghiệm thu gốc");
  });

  it("shows a dash for empty optional fields", () => {
    // Arrange
    const sparse: FileRegisterRow = {
      ...ENTRY,
      id: "f2",
      stt: 9,
      folder_path: null,
      next_action: null,
    };

    // Act
    const markup = renderToStaticMarkup(<FileRegisterTable rows={[sparse]} />);

    // Assert
    expect(markup).toContain("—");
  });

  it("shows an empty-state message when there are no entries", () => {
    // Act
    const markup = renderToStaticMarkup(<FileRegisterTable rows={[]} />);

    // Assert
    expect(markup).toContain("Chưa có file nào trong danh mục");
  });

  it("lists entries in stt order regardless of input order", () => {
    // Arrange
    const later: FileRegisterRow = { ...ENTRY, id: "f3", stt: 10, file_name: "MUON_SAU" };
    const earlier: FileRegisterRow = { ...ENTRY, id: "f4", stt: 2, file_name: "SOM_HON" };

    // Act
    const markup = renderToStaticMarkup(<FileRegisterTable rows={[later, earlier]} />);

    // Assert
    expect(markup.indexOf("SOM_HON")).toBeLessThan(markup.indexOf("MUON_SAU"));
  });
});

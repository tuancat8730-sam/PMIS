import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { DriveFileViewer } from "./drive-file-viewer";
import type { DriveFileRow } from "../../lib/drive-files";

const PDF_FILE: DriveFileRow = {
  id: "row-1",
  drive_file_id: "drive-1",
  drive_path: "bien_ban.pdf",
  file_name: "bien_ban.pdf",
  mime_type: "application/pdf",
  file_size: 2048,
  web_view_link: "https://drive.example/drive-1",
  modified_time: "2026-10-01T00:00:00Z",
  last_synced_at: "2026-11-02T08:00:00Z",
};

const DOCX_FILE: DriveFileRow = {
  ...PDF_FILE,
  id: "row-2",
  drive_file_id: "drive-2",
  drive_path: "bao_cao.docx",
  file_name: "bao_cao.docx",
};

describe("DriveFileViewer", () => {
  it("opens as an accessible dialog titled with the file name", () => {
    // Act
    const markup = renderToStaticMarkup(
      <DriveFileViewer projectId="p1" file={PDF_FILE} onClose={() => {}} />,
    );

    // Assert
    expect(markup).toContain('role="dialog"');
    expect(markup).toContain('aria-modal="true"');
    expect(markup).toContain("bien_ban.pdf");
  });

  it("shows a loading state for a PDF while its content is fetched", () => {
    // Act
    const markup = renderToStaticMarkup(
      <DriveFileViewer projectId="p1" file={PDF_FILE} onClose={() => {}} />,
    );

    // Assert
    expect(markup).toContain("Đang tải…");
  });

  it("explains that an office file cannot be previewed and offers a download", () => {
    // Act
    const markup = renderToStaticMarkup(
      <DriveFileViewer projectId="p1" file={DOCX_FILE} onClose={() => {}} />,
    );

    // Assert
    expect(markup).toContain("Loại file này không xem trực tiếp được");
    expect(markup).toContain("Tải về");
  });

  it("always offers a way to close and a download button", () => {
    // Act
    const markup = renderToStaticMarkup(
      <DriveFileViewer projectId="p1" file={PDF_FILE} onClose={() => {}} />,
    );

    // Assert
    expect(markup).toContain("Đóng");
    expect(markup).toContain("Tải về");
  });
});

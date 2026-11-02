import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { DriveFilesView } from "./drive-files-view";

describe("DriveFilesView", () => {
  it("shows the sync bar and a loading state before the list arrives", () => {
    // Act
    const markup = renderToStaticMarkup(<DriveFilesView projectId="p1" />);

    // Assert
    expect(markup).toContain("Quét ngay");
    expect(markup).toContain("Đang tải…");
  });

  it("offers the search box and the file kind filter", () => {
    // Act
    const markup = renderToStaticMarkup(<DriveFilesView projectId="p1" />);

    // Assert
    expect(markup).toContain('placeholder="Tìm theo tên file"');
    expect(markup).toContain("Tất cả loại");
    expect(markup).toContain("Âm thanh");
  });
});

import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { DriveFileGroups } from "./drive-file-groups";
import type { DriveFileRow, DriveFolderGroup } from "../../lib/drive-files";

const NESTED_FILE: DriveFileRow = {
  id: "row-1",
  drive_file_id: "drive-1",
  drive_path: "5.Nghiem thu/bien_ban.pdf",
  file_name: "bien_ban.pdf",
  mime_type: "application/pdf",
  file_size: 2048,
  web_view_link: "https://drive.example/drive-1",
  modified_time: "2026-10-01T00:00:00Z",
  last_synced_at: "2026-11-02T08:00:00Z",
};

const ROOT_FILE: DriveFileRow = {
  ...NESTED_FILE,
  id: "row-2",
  drive_file_id: "drive-2",
  drive_path: "tong_hop.pdf",
  file_name: "tong_hop.pdf",
};

const GROUPS: DriveFolderGroup[] = [
  { folder: null, files: [ROOT_FILE] },
  { folder: "5.Nghiem thu", files: [NESTED_FILE] },
];

describe("DriveFileGroups", () => {
  it("labels the root folder and shows each folder name", () => {
    // Act
    const markup = renderToStaticMarkup(<DriveFileGroups groups={GROUPS} onOpen={() => {}} />);

    // Assert
    expect(markup).toContain("Thư mục gốc");
    expect(markup).toContain("5.Nghiem thu");
  });

  it("lists each file with its size and one open button per file", () => {
    // Act
    const markup = renderToStaticMarkup(<DriveFileGroups groups={GROUPS} onOpen={() => {}} />);

    // Assert
    expect(markup).toContain("tong_hop.pdf");
    expect(markup).toContain("bien_ban.pdf");
    expect(markup).toContain("2 KB");
    expect(markup.match(/>Xem</g)).toHaveLength(2);
  });
});

import { describe, expect, it } from "vitest";

import { groupFileRegisterByFolder, type FileRegisterRow } from "./file-register";

function makeEntry(overrides: Partial<FileRegisterRow>): FileRegisterRow {
  return {
    id: "f1",
    project_id: "p1",
    stt: 1,
    folder_path: "Tài liệu lưu trữ / 1.Chủ trương",
    file_name: "file.pdf",
    file_format: "PDF",
    storage_location: "Google Drive",
    purpose: null,
    legal_status: null,
    security_ownership: null,
    next_action: null,
    drive_file_id: null,
    ...overrides,
  };
}

describe("groupFileRegisterByFolder", () => {
  it("groups entries by folder path and keeps stt order inside each group", () => {
    // Arrange
    const later = makeEntry({ id: "a", stt: 5, folder_path: "Thư mục A" });
    const earlier = makeEntry({ id: "b", stt: 2, folder_path: "Thư mục A" });
    const other = makeEntry({ id: "c", stt: 3, folder_path: "Thư mục B" });

    // Act
    const groups = groupFileRegisterByFolder([later, other, earlier]);

    // Assert
    expect(groups.map((group) => group.folder)).toEqual(["Thư mục A", "Thư mục B"]);
    expect(groups[0].rows.map((row) => row.id)).toEqual(["b", "a"]);
  });

  it("puts entries without a folder into a group whose folder is null", () => {
    // Arrange
    const orphan = makeEntry({ id: "a", folder_path: null });

    // Act
    const groups = groupFileRegisterByFolder([orphan]);

    // Assert
    expect(groups).toEqual([{ folder: null, rows: [orphan] }]);
  });

  it("does not mutate the input array", () => {
    // Arrange
    const entries = [makeEntry({ id: "b", stt: 2 }), makeEntry({ id: "a", stt: 1 })];
    const snapshot = [...entries];

    // Act
    groupFileRegisterByFolder(entries);

    // Assert
    expect(entries).toEqual(snapshot);
  });
});

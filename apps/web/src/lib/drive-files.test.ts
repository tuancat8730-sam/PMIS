import { describe, expect, it, vi } from "vitest";

import {
  driveFileKind,
  fetchDriveFileBlob,
  fetchDriveFiles,
  filterDriveFiles,
  formatFileSize,
  groupDriveFilesByFolder,
  latestSyncedAt,
  triggerDriveSync,
  type DriveFileRow,
} from "./drive-files";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function makeFile(overrides: Partial<DriveFileRow>): DriveFileRow {
  return {
    id: "row-1",
    drive_file_id: "drive-1",
    drive_path: "tong_hop.pdf",
    file_name: "tong_hop.pdf",
    mime_type: "application/pdf",
    file_size: 2048,
    web_view_link: "https://drive.example/drive-1",
    modified_time: "2026-10-01T00:00:00Z",
    last_synced_at: "2026-11-02T08:00:00Z",
    ...overrides,
  };
}

describe("fetchDriveFiles", () => {
  it("sends the bearer token and returns the file list", async () => {
    // Arrange
    const files = [makeFile({})];
    const fetchImpl = vi.fn(async () => jsonResponse(files));

    // Act
    const result = await fetchDriveFiles("p1", "token-abc", fetchImpl, "http://api.test");

    // Assert
    expect(result).toEqual(files);
    const [url, init] = fetchImpl.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("http://api.test/api/v1/projects/p1/drive/files");
    expect(init.headers).toEqual({ Authorization: "Bearer token-abc" });
  });

  it("throws with the HTTP status when the request fails", async () => {
    // Arrange
    const fetchImpl = vi.fn(async () => jsonResponse({ detail: "x" }, 403));

    // Act / Assert
    await expect(
      fetchDriveFiles("p1", "token", fetchImpl, "http://api.test"),
    ).rejects.toThrow("Không tải được danh sách file Drive (mã 403)");
  });

  it("rejects a body that is not a list", async () => {
    // Arrange
    const fetchImpl = vi.fn(async () => jsonResponse({ files: [] }));

    // Act / Assert
    await expect(
      fetchDriveFiles("p1", "token", fetchImpl, "http://api.test"),
    ).rejects.toThrow("Dữ liệu file Drive không hợp lệ");
  });
});

describe("triggerDriveSync", () => {
  it("posts to the sync endpoint with the bearer token and returns the counts", async () => {
    // Arrange
    const counts = { scanned: 3, created: 1, updated: 0, removed: 1 };
    const fetchImpl = vi.fn(async () => jsonResponse(counts));

    // Act
    const result = await triggerDriveSync("p1", "token-abc", fetchImpl, "http://api.test");

    // Assert
    expect(result).toEqual(counts);
    const [url, init] = fetchImpl.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("http://api.test/api/v1/projects/p1/drive/sync");
    expect(init.method).toBe("POST");
    expect(init.headers).toEqual({ Authorization: "Bearer token-abc" });
  });

  it.each([
    [403, "Chỉ PM của dự án mới được quét ngay"],
    [409, "Dự án chưa khai báo thư mục gốc trên Google Drive"],
    [503, "Máy chủ chưa cấu hình tài khoản dịch vụ Google Drive"],
    [502, "Google Drive đang từ chối yêu cầu, hãy thử lại sau"],
  ])("maps HTTP %i to a Vietnamese message", async (status, message) => {
    // Arrange
    const fetchImpl = vi.fn(async () => jsonResponse({ detail: "x" }, status));

    // Act / Assert
    await expect(
      triggerDriveSync("p1", "token", fetchImpl, "http://api.test"),
    ).rejects.toThrow(message);
  });
});

describe("groupDriveFilesByFolder", () => {
  it("puts root files under a null folder and nested files under their folder path", () => {
    // Arrange
    const files = [
      makeFile({ id: "a", drive_path: "5.Nghiem thu/bien_ban.pdf", file_name: "bien_ban.pdf" }),
      makeFile({ id: "b", drive_path: "tong_hop.pdf", file_name: "tong_hop.pdf" }),
    ];

    // Act
    const groups = groupDriveFilesByFolder(files);

    // Assert
    expect(groups.map((group) => group.folder)).toEqual([null, "5.Nghiem thu"]);
    expect(groups[1].files.map((file) => file.id)).toEqual(["a"]);
  });

  it("sorts folders and files by name in Vietnamese order", () => {
    // Arrange
    const files = [
      makeFile({ id: "z", drive_path: "B/zeta.pdf", file_name: "zeta.pdf" }),
      makeFile({ id: "y", drive_path: "A/yen.pdf", file_name: "yen.pdf" }),
      makeFile({ id: "x", drive_path: "A/an.pdf", file_name: "an.pdf" }),
    ];

    // Act
    const groups = groupDriveFilesByFolder(files);

    // Assert
    expect(groups.map((group) => group.folder)).toEqual(["A", "B"]);
    expect(groups[0].files.map((file) => file.file_name)).toEqual(["an.pdf", "yen.pdf"]);
  });

  it("does not modify the input array", () => {
    // Arrange
    const files = [makeFile({ id: "z", drive_path: "zeta.pdf", file_name: "zeta.pdf" })];
    const snapshot = [...files];

    // Act
    groupDriveFilesByFolder(files);

    // Assert
    expect(files).toEqual(snapshot);
  });
});

describe("driveFileKind", () => {
  it.each([
    ["bien_ban.PDF", "PDF"],
    ["bao_cao.docx", "DOCX"],
    ["so_lieu.xlsx", "XLSX"],
    ["hien_truong.jpeg", "IMAGE"],
    ["ghi_am.m4a", "AUDIO"],
    ["ghi_chu.txt", null],
  ])("classifies %s as %s", (fileName, kind) => {
    // Act / Assert
    expect(driveFileKind(fileName)).toBe(kind);
  });
});

describe("filterDriveFiles", () => {
  const files = [
    makeFile({ id: "a", file_name: "Biên bản nghiệm thu.pdf" }),
    makeFile({ id: "b", file_name: "bao_cao_tuan.docx" }),
  ];

  it("matches the name case-insensitively", () => {
    // Act / Assert
    expect(filterDriveFiles(files, "NGHIỆM", "ALL").map((file) => file.id)).toEqual(["a"]);
  });

  it("keeps only files of the selected kind", () => {
    // Act / Assert
    expect(filterDriveFiles(files, "", "DOCX").map((file) => file.id)).toEqual(["b"]);
  });

  it("returns everything when the query is blank and kind is ALL", () => {
    // Act / Assert
    expect(filterDriveFiles(files, "  ", "ALL")).toHaveLength(2);
  });
});

describe("formatFileSize", () => {
  it.each([
    [512, "512 B"],
    [2048, "2 KB"],
    [1536, "1,5 KB"],
    [5 * 1024 * 1024, "5 MB"],
  ])("formats %i bytes as %s", (bytes, text) => {
    // Act / Assert
    expect(formatFileSize(bytes)).toBe(text);
  });

  it("returns a dash when the size is unknown", () => {
    // Act / Assert
    expect(formatFileSize(null)).toBe("—");
  });
});

describe("latestSyncedAt", () => {
  it("returns the most recent sync time, or null when there are no files", () => {
    // Arrange
    const files = [
      makeFile({ id: "a", last_synced_at: "2026-11-02T08:00:00Z" }),
      makeFile({ id: "b", last_synced_at: "2026-11-02T09:30:00Z" }),
    ];

    // Act / Assert
    expect(latestSyncedAt(files)).toBe("2026-11-02T09:30:00Z");
    expect(latestSyncedAt([])).toBeNull();
  });
});

describe("fetchDriveFileBlob", () => {
  it("fetches the inline content with the bearer token", async () => {
    // Arrange
    const fetchImpl = vi.fn(async () => new Response("%PDF", { status: 200 }));

    // Act
    const blob = await fetchDriveFileBlob(
      "p1",
      "drive-1",
      "token-abc",
      { download: false },
      fetchImpl,
      "http://api.test",
    );

    // Assert
    expect(blob.size).toBe(4);
    const [url, init] = fetchImpl.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("http://api.test/api/v1/projects/p1/drive/files/drive-1/content");
    expect(init.headers).toEqual({ Authorization: "Bearer token-abc" });
  });

  it("adds the download flag when the file is requested as an attachment", async () => {
    // Arrange
    const fetchImpl = vi.fn(async () => new Response("docx", { status: 200 }));

    // Act
    await fetchDriveFileBlob("p1", "drive-1", "token", { download: true }, fetchImpl, "http://api.test");

    // Assert
    const [url] = fetchImpl.mock.calls[0] as unknown as [string];
    expect(url).toBe(
      "http://api.test/api/v1/projects/p1/drive/files/drive-1/content?download=true",
    );
  });

  it.each([
    [404, "Không tìm thấy file trong dự án này"],
    [413, "File vượt quá giới hạn xem trực tiếp"],
    [415, "Loại file này không xem trực tiếp được, hãy tải về"],
    [502, "Google Drive đang từ chối yêu cầu, hãy thử lại sau"],
  ])("maps HTTP %i to a Vietnamese message", async (status, message) => {
    // Arrange
    const fetchImpl = vi.fn(async () => new Response("{}", { status }));

    // Act / Assert
    await expect(
      fetchDriveFileBlob("p1", "drive-1", "token", { download: false }, fetchImpl, "http://api.test"),
    ).rejects.toThrow(message);
  });
});

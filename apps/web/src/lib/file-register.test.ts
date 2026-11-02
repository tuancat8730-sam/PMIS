import { describe, expect, it, vi } from "vitest";

import {
  fetchFileRegister,
  sortFileRegister,
  type FileRegisterRow,
} from "./file-register";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function makeEntry(overrides: Partial<FileRegisterRow>): FileRegisterRow {
  return {
    id: "f1",
    project_id: "p1",
    stt: 1,
    folder_path: null,
    file_name: "Checklist ho so.xlsx",
    file_format: "Excel (.xlsx)",
    storage_location: "Local & Drive",
    purpose: null,
    legal_status: null,
    security_ownership: null,
    next_action: null,
    drive_file_id: null,
    ...overrides,
  };
}

describe("fetchFileRegister", () => {
  it("sends the bearer token and returns the entry list", async () => {
    // Arrange
    const entries = [makeEntry({ stt: 1 })];
    const fetchImpl = vi.fn(async () => jsonResponse(entries));

    // Act
    const result = await fetchFileRegister("p1", "token-abc", fetchImpl, "http://api.test");

    // Assert
    expect(result).toEqual(entries);
    const [url, init] = fetchImpl.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("http://api.test/api/v1/projects/p1/file-register");
    expect(init.headers).toEqual({ Authorization: "Bearer token-abc" });
  });

  it("throws with the HTTP status when the request fails", async () => {
    // Arrange
    const fetchImpl = vi.fn(async () => jsonResponse({ detail: "x" }, 403));

    // Act
    const load = fetchFileRegister("p1", "token", fetchImpl, "http://api.test");

    // Assert
    await expect(load).rejects.toThrow("mã 403");
  });

  it("throws when the body is not a list", async () => {
    // Arrange
    const fetchImpl = vi.fn(async () => jsonResponse({ unexpected: true }));

    // Act
    const load = fetchFileRegister("p1", "token", fetchImpl, "http://api.test");

    // Assert
    await expect(load).rejects.toThrow("không hợp lệ");
  });
});

describe("sortFileRegister", () => {
  it("orders entries by stt without mutating the input", () => {
    // Arrange
    const entries = [makeEntry({ id: "b", stt: 2 }), makeEntry({ id: "a", stt: 1 })];
    const snapshot = [...entries];

    // Act
    const sorted = sortFileRegister(entries);

    // Assert
    expect(sorted.map((entry) => entry.id)).toEqual(["a", "b"]);
    expect(entries).toEqual(snapshot);
    expect(sorted).not.toBe(entries);
  });
});

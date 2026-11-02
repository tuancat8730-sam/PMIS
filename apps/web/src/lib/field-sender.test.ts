import { describe, expect, it, vi } from "vitest";

import type { FieldAction } from "./field-queue";
import { createHttpSender } from "./field-sender";

const ACTION: FieldAction = {
  id: "3f1c2a9e-0000-4000-8000-000000000001",
  deviceId: "tablet-field-001",
  method: "PATCH",
  path: "/api/v1/projects/p1/field/serials/s1/verification",
  body: { verification_status: "ĐẠT", expected_version: 1 },
  status: "PENDING",
  createdAt: "2026-11-01T02:00:00.000Z",
};

function jsonResponse(body: unknown, status: number): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function senderWith(response: Response) {
  const fetchImpl = vi.fn(async () => response);
  const send = createHttpSender({
    baseUrl: "https://api.example.gov.vn",
    getToken: () => "token-abc",
    fetchImpl,
  });
  return { send, fetchImpl };
}

describe("createHttpSender", () => {
  it("sends the action with its idempotency key and device id headers", async () => {
    // Arrange
    const { send, fetchImpl } = senderWith(jsonResponse({ id: "s1", version: 2 }, 200));

    // Act
    const result = await send(ACTION);

    // Assert
    expect(result).toEqual({ kind: "ok" });
    const [url, init] = fetchImpl.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe(`https://api.example.gov.vn${ACTION.path}`);
    const headers = new Headers(init.headers);
    expect(headers.get("Idempotency-Key")).toBe(ACTION.id);
    expect(headers.get("X-Device-Id")).toBe(ACTION.deviceId);
    expect(headers.get("Authorization")).toBe("Bearer token-abc");
    expect(init.method).toBe("PATCH");
    expect(JSON.parse(String(init.body))).toEqual(ACTION.body);
  });

  it("maps 409 to a conflict carrying the current server state", async () => {
    // Arrange
    const current = { verification_status: "ĐẠT", version: 2 };
    const { send } = senderWith(
      jsonResponse({ detail: "Xung đột", current }, 409),
    );

    // Act
    const result = await send(ACTION);

    // Assert
    expect(result).toEqual({ kind: "conflict", current });
  });

  it("maps 422 to rejected with the HTTP status", async () => {
    // Arrange
    const { send } = senderWith(jsonResponse({ detail: "Sai dữ liệu" }, 422));

    // Act
    const result = await send(ACTION);

    // Assert
    expect(result).toEqual({ kind: "rejected", httpStatus: 422 });
  });

  it("maps 5xx to retry so the action is kept for the next flush", async () => {
    // Arrange
    const { send } = senderWith(jsonResponse({ detail: "Lỗi máy chủ" }, 503));

    // Act
    const result = await send(ACTION);

    // Assert
    expect(result).toEqual({ kind: "retry" });
  });

  it("lets network errors propagate so the queue defers the action", async () => {
    // Arrange
    const fetchImpl = vi.fn(async () => {
      throw new TypeError("Failed to fetch");
    });
    const send = createHttpSender({
      baseUrl: "https://api.example.gov.vn",
      getToken: () => "token-abc",
      fetchImpl,
    });

    // Act / Assert
    await expect(send(ACTION)).rejects.toThrow(TypeError);
  });
});

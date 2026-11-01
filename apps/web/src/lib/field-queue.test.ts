import { describe, expect, it, vi } from "vitest";

import {
  createFieldQueue,
  type FieldAction,
  type FieldQueueStore,
  type SendResult,
} from "./field-queue";

const DEVICE_ID = "tablet-field-001";

function createMemoryStore(): FieldQueueStore & { rows: Map<string, FieldAction> } {
  const rows = new Map<string, FieldAction>();
  return {
    rows,
    async list() {
      return [...rows.values()];
    },
    async put(action) {
      rows.set(action.id, action);
    },
    async remove(id) {
      rows.delete(id);
    },
  };
}

function sequentialIds(): () => string {
  let counter = 0;
  return () => {
    counter += 1;
    return `key-${counter}`;
  };
}

describe("createFieldQueue.enqueue", () => {
  it("keeps the action as pending in the store when the device is offline", async () => {
    // Arrange
    const store = createMemoryStore();
    const queue = createFieldQueue({ store, send: vi.fn(), newId: sequentialIds() });

    // Act
    const action = await queue.enqueue({
      deviceId: DEVICE_ID,
      method: "PATCH",
      path: "/api/v1/projects/p1/field/serials/s1/verification",
      body: { verification_status: "ĐẠT", expected_version: 1 },
    });

    // Assert
    expect(action.status).toBe("PENDING");
    expect(store.rows.get(action.id)).toEqual(action);
  });
});

describe("createFieldQueue.flush", () => {
  it("sends each pending action once and removes it after success", async () => {
    // Arrange
    const store = createMemoryStore();
    const send = vi.fn<(action: FieldAction) => Promise<SendResult>>(async () => ({
      kind: "ok",
    }));
    const queue = createFieldQueue({ store, send, newId: sequentialIds() });
    await queue.enqueue({ deviceId: DEVICE_ID, method: "PATCH", path: "/a", body: {} });

    // Act
    const first = await queue.flush();
    const second = await queue.flush();

    // Assert
    expect(first).toEqual({ sent: 1, conflicted: 0, rejected: 0, deferred: 0 });
    expect(second.sent).toBe(0);
    expect(send).toHaveBeenCalledTimes(1);
    expect(store.rows.size).toBe(0);
  });

  it("retries a failed send with the same idempotency key", async () => {
    // Arrange
    const store = createMemoryStore();
    const send = vi
      .fn<(action: FieldAction) => Promise<SendResult>>()
      .mockResolvedValueOnce({ kind: "retry" })
      .mockResolvedValueOnce({ kind: "ok" });
    const queue = createFieldQueue({ store, send, newId: sequentialIds() });
    const action = await queue.enqueue({
      deviceId: DEVICE_ID,
      method: "PATCH",
      path: "/a",
      body: {},
    });

    // Act
    const offline = await queue.flush();
    const online = await queue.flush();

    // Assert
    expect(offline).toEqual({ sent: 0, conflicted: 0, rejected: 0, deferred: 1 });
    expect(online.sent).toBe(1);
    expect(send.mock.calls[0][0].id).toBe(action.id);
    expect(send.mock.calls[1][0].id).toBe(action.id);
  });

  it("stops at the first deferred action so later actions keep their order", async () => {
    // Arrange
    const store = createMemoryStore();
    const send = vi.fn<(action: FieldAction) => Promise<SendResult>>(async () => ({
      kind: "retry",
    }));
    const queue = createFieldQueue({ store, send, newId: sequentialIds() });
    await queue.enqueue({ deviceId: DEVICE_ID, method: "PATCH", path: "/a", body: {} });
    await queue.enqueue({ deviceId: DEVICE_ID, method: "PATCH", path: "/b", body: {} });

    // Act
    const result = await queue.flush();

    // Assert
    expect(result.deferred).toBe(1);
    expect(send).toHaveBeenCalledTimes(1);
    expect(send.mock.calls[0][0].path).toBe("/a");
  });

  it("marks a conflicting action and does not resend it on the next flush", async () => {
    // Arrange
    const store = createMemoryStore();
    const send = vi.fn<(action: FieldAction) => Promise<SendResult>>(async () => ({
      kind: "conflict",
      current: { delivery_status: "INSTALLED", version: 3 },
    }));
    const queue = createFieldQueue({ store, send, newId: sequentialIds() });
    const action = await queue.enqueue({
      deviceId: DEVICE_ID,
      method: "PATCH",
      path: "/a",
      body: {},
    });

    // Act
    const first = await queue.flush();
    const second = await queue.flush();

    // Assert
    expect(first.conflicted).toBe(1);
    expect(second.conflicted).toBe(0);
    expect(send).toHaveBeenCalledTimes(1);
    expect(store.rows.get(action.id)?.status).toBe("CONFLICT");
    expect(store.rows.get(action.id)?.conflictCurrent).toEqual({
      delivery_status: "INSTALLED",
      version: 3,
    });
  });

  it("marks a rejected action without retrying it", async () => {
    // Arrange
    const store = createMemoryStore();
    const send = vi.fn<(action: FieldAction) => Promise<SendResult>>(async () => ({
      kind: "rejected",
      httpStatus: 422,
    }));
    const queue = createFieldQueue({ store, send, newId: sequentialIds() });
    const action = await queue.enqueue({
      deviceId: DEVICE_ID,
      method: "PATCH",
      path: "/a",
      body: {},
    });

    // Act
    const result = await queue.flush();

    // Assert
    expect(result.rejected).toBe(1);
    expect(store.rows.get(action.id)?.status).toBe("REJECTED");
  });

  it("treats a thrown network error as deferred, not as a failure", async () => {
    // Arrange
    const store = createMemoryStore();
    const send = vi.fn<(action: FieldAction) => Promise<SendResult>>(async () => {
      throw new TypeError("Failed to fetch");
    });
    const queue = createFieldQueue({ store, send, newId: sequentialIds() });
    await queue.enqueue({ deviceId: DEVICE_ID, method: "PATCH", path: "/a", body: {} });

    // Act
    const result = await queue.flush();

    // Assert
    expect(result.deferred).toBe(1);
    expect(store.rows.size).toBe(1);
  });
});

describe("createFieldQueue.listPending", () => {
  it("returns only actions still waiting to be sent", async () => {
    // Arrange
    const store = createMemoryStore();
    const send = vi
      .fn<(action: FieldAction) => Promise<SendResult>>()
      .mockResolvedValueOnce({ kind: "ok" })
      .mockResolvedValueOnce({ kind: "retry" });
    const queue = createFieldQueue({ store, send, newId: sequentialIds() });
    await queue.enqueue({ deviceId: DEVICE_ID, method: "PATCH", path: "/a", body: {} });
    await queue.enqueue({ deviceId: DEVICE_ID, method: "PATCH", path: "/b", body: {} });
    await queue.flush();

    // Act
    const pending = await queue.listPending();

    // Assert
    expect(pending.map((action) => action.path)).toEqual(["/b"]);
  });
});

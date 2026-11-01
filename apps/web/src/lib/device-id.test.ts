import { describe, expect, it } from "vitest";

import { DEVICE_ID_STORAGE_KEY, getOrCreateDeviceId } from "./device-id";

function memoryStorage(initial: Record<string, string> = {}) {
  const data = new Map<string, string>(Object.entries(initial));
  return {
    getItem: (key: string) => data.get(key) ?? null,
    setItem: (key: string, value: string) => {
      data.set(key, value);
    },
  };
}

describe("getOrCreateDeviceId", () => {
  it("returns the stored id when the device already has one", () => {
    // Arrange
    const storage = memoryStorage({ [DEVICE_ID_STORAGE_KEY]: "tablet-existing-01" });

    // Act
    const id = getOrCreateDeviceId(storage, () => "tablet-new-000000001");

    // Assert
    expect(id).toBe("tablet-existing-01");
  });

  it("creates and stores a new id once when none exists", () => {
    // Arrange
    const storage = memoryStorage();

    // Act
    const first = getOrCreateDeviceId(storage, () => "tablet-new-000000001");
    const second = getOrCreateDeviceId(storage, () => "tablet-other-00000002");

    // Assert
    expect(first).toBe("tablet-new-000000001");
    expect(second).toBe("tablet-new-000000001");
  });

  it("falls back to an in-memory id when storage throws", () => {
    // Arrange
    const brokenStorage = {
      getItem: () => {
        throw new Error("denied");
      },
      setItem: () => {
        throw new Error("denied");
      },
    };

    // Act
    const id = getOrCreateDeviceId(brokenStorage, () => "tablet-memory-000001");

    // Assert
    expect(id).toBe("tablet-memory-000001");
  });
});

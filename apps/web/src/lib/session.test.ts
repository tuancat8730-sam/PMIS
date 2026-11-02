import { describe, expect, it } from "vitest";

import { SESSION_TOKEN_STORAGE_KEY } from "./command-center";
import { saveSessionToken, type TokenStorage } from "./session";

function createMemoryStorage(): TokenStorage & { values: Map<string, string> } {
  const values = new Map<string, string>();
  return {
    values,
    setItem: (key: string, value: string) => {
      values.set(key, value);
    },
  };
}

describe("saveSessionToken", () => {
  it("stores the token under the Command Center session key", () => {
    // Arrange
    const storage = createMemoryStorage();

    // Act
    saveSessionToken("jwt-abc", storage);

    // Assert
    expect(storage.values.get(SESSION_TOKEN_STORAGE_KEY)).toBe("jwt-abc");
  });

  it("explains the failure when the browser refuses to store the token", () => {
    // Arrange
    const blockedStorage: TokenStorage = {
      setItem: () => {
        throw new DOMException("quota exceeded", "QuotaExceededError");
      },
    };

    // Act & Assert
    expect(() => saveSessionToken("jwt-abc", blockedStorage)).toThrow(
      "Trình duyệt không lưu được phiên đăng nhập",
    );
  });
});

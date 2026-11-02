export const DEVICE_ID_STORAGE_KEY = "pmis.field.deviceId";

export interface KeyValueStorage {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
}

// Bộ nhớ tạm của tiến trình khi trình duyệt chặn localStorage (chế độ riêng tư, cookie bị tắt).
let memoryFallbackId: string | null = null;

function createDeviceId(): string {
  return `tablet-${crypto.randomUUID()}`;
}

/**
 * Định danh thiết bị sinh một lần rồi giữ trong localStorage (G2).
 * Không lưu thông tin cá nhân trong định danh này.
 */
export function getOrCreateDeviceId(
  storage: KeyValueStorage | null = safeLocalStorage(),
  newId: () => string = createDeviceId,
): string {
  try {
    const stored = storage?.getItem(DEVICE_ID_STORAGE_KEY);
    if (stored) {
      return stored;
    }
    const created = newId();
    storage?.setItem(DEVICE_ID_STORAGE_KEY, created);
    return created;
  } catch {
    memoryFallbackId ??= newId();
    return memoryFallbackId;
  }
}

function safeLocalStorage(): KeyValueStorage | null {
  try {
    return typeof localStorage === "undefined" ? null : localStorage;
  } catch {
    return null;
  }
}

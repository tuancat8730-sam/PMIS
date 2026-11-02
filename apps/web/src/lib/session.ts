import { SESSION_TOKEN_STORAGE_KEY } from "./command-center";

const STORAGE_ERROR_MESSAGE = "Trình duyệt không lưu được phiên đăng nhập";

export interface TokenStorage {
  setItem: (key: string, value: string) => void;
}

/** Lưu JWT để các trang như Command Center đọc lại. Ném lỗi có thông báo tiếng Việt nếu trình duyệt chặn. */
export function saveSessionToken(
  token: string,
  storage: TokenStorage = window.localStorage,
): void {
  try {
    storage.setItem(SESSION_TOKEN_STORAGE_KEY, token);
  } catch {
    throw new Error(STORAGE_ERROR_MESSAGE);
  }
}

import type { FieldAction, SendResult } from "./field-queue";

export interface HttpSenderOptions {
  readonly baseUrl: string;
  readonly getToken: () => string | null;
  readonly fetchImpl?: typeof fetch;
}

const HTTP_CONFLICT = 409;
const HTTP_SERVER_ERROR_MIN = 500;

interface ConflictBody {
  readonly current?: unknown;
}

function isConflictBody(value: unknown): value is ConflictBody {
  return typeof value === "object" && value !== null;
}

async function readConflictCurrent(response: Response): Promise<unknown> {
  try {
    const body: unknown = await response.json();
    return isConflictBody(body) ? body.current : undefined;
  } catch {
    // Phản hồi 409 không đọc được JSON: vẫn là xung đột, chỉ thiếu trạng thái hiện tại.
    return undefined;
  }
}

function buildHeaders(action: FieldAction, token: string | null): Headers {
  const headers = new Headers({
    "Content-Type": "application/json",
    "Idempotency-Key": action.id,
    "X-Device-Id": action.deviceId,
  });
  if (token !== null) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  return headers;
}

async function toSendResult(response: Response): Promise<SendResult> {
  if (response.ok) {
    return { kind: "ok" };
  }
  if (response.status === HTTP_CONFLICT) {
    return { kind: "conflict", current: await readConflictCurrent(response) };
  }
  if (response.status >= HTTP_SERVER_ERROR_MIN) {
    return { kind: "retry" };
  }
  return { kind: "rejected", httpStatus: response.status };
}

/**
 * Gửi một thao tác tới API. Lỗi mạng được ném lên để hàng đợi giữ lại thao tác.
 */
export function createHttpSender(
  options: HttpSenderOptions,
): (action: FieldAction) => Promise<SendResult> {
  const fetchImpl = options.fetchImpl ?? fetch;
  const base = options.baseUrl.replace(/\/+$/, "");

  return async (action: FieldAction): Promise<SendResult> => {
    const response = await fetchImpl(`${base}${action.path}`, {
      method: action.method,
      headers: buildHeaders(action, options.getToken()),
      body: JSON.stringify(action.body),
      cache: "no-store",
    });
    return toSendResult(response);
  };
}

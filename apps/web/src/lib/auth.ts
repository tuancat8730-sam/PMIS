import { z } from "zod";

import { resolveApiUrl } from "./api";

export const LOGIN_PATH = "/api/v1/auth/login";

const CONNECTION_ERROR_MESSAGE = "Không kết nối được máy chủ";
const INVALID_RESPONSE_MESSAGE = "Phản hồi đăng nhập không hợp lệ";
const UNKNOWN_FAILURE_MESSAGE = "Đăng nhập thất bại, vui lòng thử lại";

const loginSchema = z.object({
  email: z.email({ message: "Email không hợp lệ" }),
  password: z.string().min(1, { message: "Vui lòng nhập mật khẩu" }),
});

export type LoginInput = z.infer<typeof loginSchema>;

interface TokenBody {
  access_token: string;
}

function isTokenBody(value: unknown): value is TokenBody {
  return (
    typeof value === "object" &&
    value !== null &&
    "access_token" in value &&
    typeof value.access_token === "string"
  );
}

/** Kiểm tra dữ liệu form trước khi gửi lên API. */
export function parseLoginInput(raw: unknown) {
  return loginSchema.safeParse(raw);
}

/** Lấy thông báo `detail` từ body lỗi của FastAPI, nếu có. */
async function readErrorDetail(response: Response): Promise<string | null> {
  try {
    const body: unknown = await response.json();
    if (typeof body === "object" && body !== null && "detail" in body) {
      return typeof body.detail === "string" ? body.detail : null;
    }
    return null;
  } catch {
    return null;
  }
}

async function readAccessToken(response: Response): Promise<string> {
  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new Error(detail ?? UNKNOWN_FAILURE_MESSAGE);
  }
  const body: unknown = await response.json().catch(() => null);
  if (!isTokenBody(body)) {
    throw new Error(INVALID_RESPONSE_MESSAGE);
  }
  return body.access_token;
}

/** Đăng nhập bằng form-encoded (OAuth2 password flow) và trả về JWT. */
export async function requestLoginToken(
  input: LoginInput,
  fetchImpl: typeof fetch = fetch,
  baseUrl: string | undefined = process.env.NEXT_PUBLIC_API_URL,
): Promise<string> {
  const body = new URLSearchParams({ username: input.email, password: input.password });
  let response: Response;
  try {
    response = await fetchImpl(resolveApiUrl(LOGIN_PATH, baseUrl), {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
      cache: "no-store",
    });
  } catch {
    throw new Error(CONNECTION_ERROR_MESSAGE);
  }
  return readAccessToken(response);
}

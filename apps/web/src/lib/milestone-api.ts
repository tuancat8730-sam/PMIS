import { resolveApiUrl } from "./api";
import type { MilestoneUpdatePayload, TaskPayload, TaskStatus } from "./milestone-forms";

const FALLBACK_ERROR_MESSAGE = "Không lưu được thay đổi";

type FetchImpl = typeof fetch;

interface RequestOptions {
  method: "POST" | "PATCH" | "DELETE";
  path: string;
  token: string;
  body?: unknown;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

async function errorMessageFrom(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json();
    if (isRecord(body) && typeof body.detail === "string") {
      return body.detail;
    }
  } catch {
    // Phản hồi không phải JSON: dùng thông điệp chung bên dưới.
  }
  return `${FALLBACK_ERROR_MESSAGE} (mã ${response.status})`;
}

async function sendWrite(
  options: RequestOptions,
  fetchImpl: FetchImpl,
  baseUrl: string | undefined,
): Promise<void> {
  const hasBody = options.body !== undefined;
  const response = await fetchImpl(resolveApiUrl(options.path, baseUrl), {
    method: options.method,
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${options.token}`,
      ...(hasBody ? { "Content-Type": "application/json" } : {}),
    },
    ...(hasBody ? { body: JSON.stringify(options.body) } : {}),
  });
  if (!response.ok) {
    throw new Error(await errorMessageFrom(response));
  }
}

function milestonePath(projectId: string, milestoneId: string): string {
  return `/api/v1/projects/${encodeURIComponent(projectId)}/milestones/${encodeURIComponent(milestoneId)}`;
}

export function updateMilestone(
  projectId: string,
  milestoneId: string,
  payload: Partial<MilestoneUpdatePayload>,
  token: string,
  fetchImpl: FetchImpl = fetch,
  baseUrl: string | undefined = process.env.NEXT_PUBLIC_API_URL,
): Promise<void> {
  return sendWrite(
    { method: "PATCH", path: milestonePath(projectId, milestoneId), token, body: payload },
    fetchImpl,
    baseUrl,
  );
}

export function createTask(
  projectId: string,
  milestoneId: string,
  payload: TaskPayload,
  token: string,
  fetchImpl: FetchImpl = fetch,
  baseUrl: string | undefined = process.env.NEXT_PUBLIC_API_URL,
): Promise<void> {
  return sendWrite(
    { method: "POST", path: `${milestonePath(projectId, milestoneId)}/tasks`, token, body: payload },
    fetchImpl,
    baseUrl,
  );
}

export function updateTask(
  projectId: string,
  milestoneId: string,
  taskId: string,
  payload: Partial<{ status: TaskStatus }> & Partial<TaskPayload>,
  token: string,
  fetchImpl: FetchImpl = fetch,
  baseUrl: string | undefined = process.env.NEXT_PUBLIC_API_URL,
): Promise<void> {
  const path = `${milestonePath(projectId, milestoneId)}/tasks/${encodeURIComponent(taskId)}`;
  return sendWrite({ method: "PATCH", path, token, body: payload }, fetchImpl, baseUrl);
}

export function deleteTask(
  projectId: string,
  milestoneId: string,
  taskId: string,
  token: string,
  fetchImpl: FetchImpl = fetch,
  baseUrl: string | undefined = process.env.NEXT_PUBLIC_API_URL,
): Promise<void> {
  const path = `${milestonePath(projectId, milestoneId)}/tasks/${encodeURIComponent(taskId)}`;
  return sendWrite({ method: "DELETE", path, token }, fetchImpl, baseUrl);
}

export function createNote(
  projectId: string,
  milestoneId: string,
  body: string,
  token: string,
  fetchImpl: FetchImpl = fetch,
  baseUrl: string | undefined = process.env.NEXT_PUBLIC_API_URL,
): Promise<void> {
  return sendWrite(
    { method: "POST", path: `${milestonePath(projectId, milestoneId)}/notes`, token, body: { body } },
    fetchImpl,
    baseUrl,
  );
}

interface MemberEntry {
  user_id: string;
  role: string;
}

function isMemberEntry(value: unknown): value is MemberEntry {
  return isRecord(value) && typeof value.user_id === "string" && typeof value.role === "string";
}

/** Vai trò của chính người dùng trong dự án, hoặc null nếu không phải thành viên. */
export async function fetchMyProjectRole(
  projectId: string,
  userId: string,
  token: string,
  fetchImpl: FetchImpl = fetch,
  baseUrl: string | undefined = process.env.NEXT_PUBLIC_API_URL,
): Promise<string | null> {
  const path = `/api/v1/projects/${encodeURIComponent(projectId)}/members`;
  const response = await fetchImpl(resolveApiUrl(path, baseUrl), {
    cache: "no-store",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(`Không tải được thành viên dự án (mã ${response.status})`);
  }
  const body: unknown = await response.json();
  if (!Array.isArray(body)) {
    throw new Error("Dữ liệu thành viên dự án không hợp lệ");
  }
  const member = body.filter(isMemberEntry).find((entry) => entry.user_id === userId);
  return member?.role ?? null;
}

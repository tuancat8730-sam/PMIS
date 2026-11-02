import { resolveApiUrl } from "./api";
import type { ProjectSummary } from "./overview";

const PROJECTS_PATH = "/api/v1/projects";

function isProjectList(value: unknown): value is ProjectSummary[] {
  return Array.isArray(value);
}

/** Tải danh sách dự án mà người dùng được xem. Ném lỗi tiếng Việt nếu API lỗi hoặc dữ liệu sai hình dạng. */
export async function fetchProjects(
  token: string,
  fetchImpl: typeof fetch = fetch,
  baseUrl: string | undefined = process.env.NEXT_PUBLIC_API_URL,
): Promise<ProjectSummary[]> {
  const response = await fetchImpl(resolveApiUrl(PROJECTS_PATH, baseUrl), {
    cache: "no-store",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(`Không tải được danh sách dự án (mã ${response.status})`);
  }
  const payload: unknown = await response.json();
  if (!isProjectList(payload)) {
    throw new Error("Dữ liệu danh sách dự án không hợp lệ");
  }
  return payload;
}

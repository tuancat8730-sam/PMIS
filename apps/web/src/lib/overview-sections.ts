import { resolveApiUrl } from "./api";

export type BudgetCategory =
  | "SOFTWARE"
  | "PROJECT_MANAGEMENT"
  | "CONSULTING"
  | "OTHER"
  | "CONTINGENCY";

export interface BudgetItemRow {
  id: string;
  project_id: string;
  category: BudgetCategory;
  label: string;
  amount: string;
  note: string | null;
  sort_order: number;
}

export interface TechnicalRequirementRow {
  id: string;
  project_id: string;
  sort_order: number;
  item: string;
  standard: string | null;
  legal_basis: string | null;
  solution: string | null;
  responsibility: string | null;
  acceptance_criteria: string | null;
  related_risk: string | null;
  monitoring_status: string | null;
}

export interface OverviewSections {
  budgetItems: BudgetItemRow[];
  requirements: TechnicalRequirementRow[];
}

const ISO_DATE_PATTERN = /^(\d{4})-(\d{2})-(\d{2})$/;

/** Đổi ngày ISO (yyyy-mm-dd) sang dd/mm/yyyy. Cắt chuỗi thay vì dựng Date để không lệch múi giờ. */
export function formatDateVi(isoDate: string | null): string | null {
  if (isoDate === null) {
    return null;
  }
  const match = ISO_DATE_PATTERN.exec(isoDate);
  if (match === null) {
    return isoDate;
  }
  const [, year, month, day] = match;
  return `${day}/${month}/${year}`;
}

async function getSection<T>(
  path: string,
  token: string,
  fetchImpl: typeof fetch,
  baseUrl: string | undefined,
): Promise<T[]> {
  const response = await fetchImpl(resolveApiUrl(path, baseUrl), {
    cache: "no-store",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(`Không tải được tổng quan dự án (mã ${response.status})`);
  }
  const body: unknown = await response.json();
  if (!Array.isArray(body)) {
    throw new Error("Dữ liệu tổng quan dự án không hợp lệ");
  }
  return body as T[];
}

/** Tải song song khoản chi và yêu cầu kỹ thuật của dự án. Ném lỗi nếu một lời gọi lỗi. */
export async function fetchOverviewSections(
  projectId: string,
  token: string,
  fetchImpl: typeof fetch = fetch,
  baseUrl: string | undefined = process.env.NEXT_PUBLIC_API_URL,
): Promise<OverviewSections> {
  const base = `/api/v1/projects/${encodeURIComponent(projectId)}`;
  const [budgetItems, requirements] = await Promise.all([
    getSection<BudgetItemRow>(`${base}/budget-items`, token, fetchImpl, baseUrl),
    getSection<TechnicalRequirementRow>(
      `${base}/technical-requirements`,
      token,
      fetchImpl,
      baseUrl,
    ),
  ]);
  return { budgetItems, requirements };
}

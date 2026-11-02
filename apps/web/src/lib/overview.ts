import { resolveApiUrl } from "./api";

export type LegalDecisionKind =
  | "PROJECT_APPROVAL"
  | "BCKTKT_APPROVAL"
  | "BUDGET_APPROVAL"
  | "KHLCNT_APPROVAL"
  | "BIDDING_RESULT_APPROVAL"
  | "SUPERVISION_ASSIGNMENT";

export interface ProjectSummary {
  id: string;
  code: string;
  name: string;
  investor_name: string;
  decision_authority: string | null;
  total_investment: string;
  start_date: string | null;
  end_date: string | null;
}

export interface LegalDecisionRow {
  id: string;
  kind: LegalDecisionKind;
  decision_no: string;
  decision_date: string | null;
  issuing_authority: string | null;
  amount: string | null;
  funding_source: string | null;
  execution_period: string | null;
  note: string | null;
}

export interface ContractSummaryRow {
  id: string;
  package_name: string;
  package_kind: string;
  contract_number: string | null;
  signed_date: string | null;
  expiration_date: string | null;
  contract_value: string;
}

export interface ProjectOverview {
  project: ProjectSummary;
  decisions: LegalDecisionRow[];
  contracts: ContractSummaryRow[];
}

const DECISION_KIND_LABELS: Record<LegalDecisionKind, string> = {
  PROJECT_APPROVAL: "Quyết định phê duyệt dự án",
  BCKTKT_APPROVAL: "Quyết định phê duyệt BCKTKT",
  BUDGET_APPROVAL: "Quyết định phê duyệt dự toán",
  KHLCNT_APPROVAL: "Quyết định phê duyệt KHLCNT",
  BIDDING_RESULT_APPROVAL: "Quyết định phê duyệt kết quả LCNT",
  SUPERVISION_ASSIGNMENT: "Quyết định chỉ định tư vấn giám sát",
};

const VND_FORMATTER = new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 0 });

async function getJson(
  path: string,
  token: string,
  fetchImpl: typeof fetch,
  baseUrl: string | undefined,
): Promise<unknown> {
  const response = await fetchImpl(resolveApiUrl(path, baseUrl), {
    cache: "no-store",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(`Không tải được tổng quan dự án (mã ${response.status})`);
  }
  return response.json();
}

function isProjectSummary(value: unknown): value is ProjectSummary {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** Tải song song thông tin dự án, quyết định pháp lý và hợp đồng. Ném lỗi nếu một lời gọi lỗi. */
export async function fetchProjectOverview(
  projectId: string,
  token: string,
  fetchImpl: typeof fetch = fetch,
  baseUrl: string | undefined = process.env.NEXT_PUBLIC_API_URL,
): Promise<ProjectOverview> {
  const base = `/api/v1/projects/${encodeURIComponent(projectId)}`;
  const [project, decisions, contracts] = await Promise.all([
    getJson(base, token, fetchImpl, baseUrl),
    getJson(`${base}/legal-decisions`, token, fetchImpl, baseUrl),
    getJson(`${base}/contracts`, token, fetchImpl, baseUrl),
  ]);
  if (!isProjectSummary(project) || !Array.isArray(decisions) || !Array.isArray(contracts)) {
    throw new Error("Dữ liệu tổng quan dự án không hợp lệ");
  }
  return {
    project,
    decisions: decisions as LegalDecisionRow[],
    contracts: contracts as ContractSummaryRow[],
  };
}

const DECISION_KIND_ORDER: readonly LegalDecisionKind[] = [
  "PROJECT_APPROVAL",
  "BCKTKT_APPROVAL",
  "BUDGET_APPROVAL",
  "KHLCNT_APPROVAL",
  "BIDDING_RESULT_APPROVAL",
  "SUPERVISION_ASSIGNMENT",
];

export interface DecisionKindGroup {
  kind: LegalDecisionKind;
  rows: LegalDecisionRow[];
}

/** Nhóm quyết định theo loại theo thứ tự cố định, quyết định phê duyệt dự án đứng đầu. Bỏ loại không có dòng nào. */
export function groupDecisionsByKind(decisions: readonly LegalDecisionRow[]): DecisionKindGroup[] {
  return DECISION_KIND_ORDER.flatMap((kind) => {
    const rows = decisions.filter((decision) => decision.kind === kind);
    return rows.length === 0 ? [] : [{ kind, rows }];
  });
}

/** Định dạng số tiền (chuỗi thập phân từ API) theo vi-VN, ví dụ "5.999.498.939 đ". */
export function formatVnd(amount: string): string {
  return `${VND_FORMATTER.format(Number(amount))} đ`;
}

export function decisionKindLabel(kind: LegalDecisionKind): string {
  return DECISION_KIND_LABELS[kind];
}

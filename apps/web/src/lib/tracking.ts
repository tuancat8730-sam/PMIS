import { resolveApiUrl } from "./api";

export type MilestoneDisplayStatus =
  | "NOT_STARTED"
  | "IN_PROGRESS"
  | "COMPLETED"
  | "AT_RISK"
  | "OVERDUE";
export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "VERY_HIGH";

export interface ScheduleRow {
  id: string;
  project_id: string;
  code: string;
  name: string;
  baseline_start: string | null;
  baseline_end: string;
  adjusted_start: string | null;
  adjusted_end: string | null;
  actual_end: string | null;
  is_hard_deadline: boolean;
  progress_percent: string;
  status: string;
  display_status: MilestoneDisplayStatus;
  slippage_days: number;
  responsible_party: string | null;
  evidence_summary: string | null;
  deliverables: string | null;
  acceptance_conditions: string | null;
  tvgs_checkpoint: string | null;
  pm_comment: string | null;
}

export interface ScheduleMatrixData {
  total: number;
  rows: ScheduleRow[];
}

export interface RiskRow {
  id: string;
  code: string;
  record_type: string;
  title: string;
  status: string;
  owner: string | null;
  due_date: string | null;
  impact: RiskLevel | null;
  likelihood: RiskLevel | null;
  score: number | null;
  coordinating_units: string | null;
}

export interface RiskMatrixData {
  total: number;
  rows: RiskRow[];
}

const RISK_LEVEL_LABELS: Record<RiskLevel, string> = {
  LOW: "Thấp",
  MEDIUM: "Trung bình",
  HIGH: "Cao",
  VERY_HIGH: "Rất cao",
};

const MILESTONE_STATUS_LABELS: Record<MilestoneDisplayStatus, string> = {
  NOT_STARTED: "Chưa bắt đầu",
  IN_PROGRESS: "Đang thực hiện",
  COMPLETED: "Hoàn thành",
  AT_RISK: "Có nguy cơ",
  OVERDUE: "Quá hạn",
};

const DATE_PARTS_PATTERN = /^(\d{4})-(\d{2})-(\d{2})$/;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

/** Kiểm tra biên tối thiểu trước khi đưa dữ liệu vào giao diện. */
function isScheduleMatrix(value: unknown): value is ScheduleMatrixData {
  return isRecord(value) && typeof value.total === "number" && Array.isArray(value.rows);
}

function isRiskMatrix(value: unknown): value is RiskMatrixData {
  return isRecord(value) && typeof value.total === "number" && Array.isArray(value.rows);
}

async function fetchMatrix<T>(
  projectId: string,
  suffix: string,
  token: string,
  guard: (value: unknown) => value is T,
  fetchImpl: typeof fetch,
  baseUrl: string | undefined,
): Promise<T> {
  const path = `/api/v1/projects/${encodeURIComponent(projectId)}/${suffix}`;
  const response = await fetchImpl(resolveApiUrl(path, baseUrl), {
    cache: "no-store",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(`Không tải được ${suffix} (mã ${response.status})`);
  }
  const body: unknown = await response.json();
  if (!guard(body)) {
    throw new Error(`Dữ liệu ${suffix} không hợp lệ`);
  }
  return body;
}

export function fetchScheduleMatrix(
  projectId: string,
  token: string,
  fetchImpl: typeof fetch = fetch,
  baseUrl: string | undefined = process.env.NEXT_PUBLIC_API_URL,
): Promise<ScheduleMatrixData> {
  return fetchMatrix(projectId, "schedule-matrix", token, isScheduleMatrix, fetchImpl, baseUrl);
}

export function fetchRiskMatrix(
  projectId: string,
  token: string,
  fetchImpl: typeof fetch = fetch,
  baseUrl: string | undefined = process.env.NEXT_PUBLIC_API_URL,
): Promise<RiskMatrixData> {
  return fetchMatrix(projectId, "risk-matrix", token, isRiskMatrix, fetchImpl, baseUrl);
}

/** Nhãn tiếng Việt cho mức tác động hoặc khả năng. `null` nghĩa là chưa đánh giá. */
export function riskLevelLabel(level: RiskLevel | null): string {
  return level === null ? "Chưa đánh giá" : RISK_LEVEL_LABELS[level];
}

/** Ngày ISO (yyyy-mm-dd) sang dd/mm/yyyy. Không dùng Date để tránh lệch múi giờ. */
export function formatDateVi(isoDate: string | null): string {
  if (isoDate === null) {
    return "—";
  }
  const match = DATE_PARTS_PATTERN.exec(isoDate);
  if (match === null) {
    return isoDate;
  }
  const [, year, month, day] = match;
  return `${day}/${month}/${year}`;
}

/** Nhãn tiếng Việt cho trạng thái hiển thị của mốc (đã gồm nguy cơ và quá hạn). */
export function milestoneStatusLabel(status: MilestoneDisplayStatus): string {
  return MILESTONE_STATUS_LABELS[status];
}

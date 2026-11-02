import { resolveApiUrl } from "./api";

export const COMMAND_CENTER_PATH = "/api/v1/command-center";
/** Khóa localStorage lưu JWT đăng nhập. Giữ đồng bộ với phiên đăng nhập của các trang khác. */
export const SESSION_TOKEN_STORAGE_KEY = "pmis.field.token";

export type ProjectHealth = "ON_TRACK" | "AT_RISK" | "DELAYED" | "CRITICAL" | "COMPLETED";
export type RedAlertSource = "MILESTONE" | "RISK";
export type CountdownStatus = "WARNING" | "EXPIRED";

export interface CommandCenterKpi {
  contract_value_by_kind: Record<string, string>;
  contract_value_total: string;
  running_project_count: number;
  beneficiary_unit_count: number;
  pending_signature_count: number | null;
  red_alert_count: number;
}

export interface ProjectHealthRow {
  id: string;
  code: string;
  short_name: string;
  health: ProjectHealth;
  red_alert_count: number;
  max_slippage_days: number;
}

export interface RedAlertRow {
  project_code: string;
  source: RedAlertSource;
  code: string;
  title: string;
  due_date: string;
}

export interface ContractCountdownRow {
  project_code: string;
  contract_number: string | null;
  status: CountdownStatus;
  expiration_date: string;
  days_remaining: number;
}

export interface CommandCenterData {
  as_of: string;
  kpi: CommandCenterKpi;
  projects: ProjectHealthRow[];
  red_alerts: RedAlertRow[];
  contract_countdowns: ContractCountdownRow[];
}

const BILLION_VND = 1_000_000_000;
const BILLION_FORMATTER = new Intl.NumberFormat("vi-VN", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

/** Kiểm tra biên dữ liệu từ API trước khi đưa vào giao diện. */
function isCommandCenterData(value: unknown): value is CommandCenterData {
  return (
    isRecord(value) &&
    typeof value.as_of === "string" &&
    isRecord(value.kpi) &&
    Array.isArray(value.projects) &&
    Array.isArray(value.red_alerts) &&
    Array.isArray(value.contract_countdowns)
  );
}

export async function fetchCommandCenter(
  token: string,
  fetchImpl: typeof fetch = fetch,
  baseUrl: string | undefined = process.env.NEXT_PUBLIC_API_URL,
): Promise<CommandCenterData> {
  const response = await fetchImpl(resolveApiUrl(COMMAND_CENTER_PATH, baseUrl), {
    cache: "no-store",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(`Command Center trả về mã ${response.status}`);
  }
  const body: unknown = await response.json();
  if (!isCommandCenterData(body)) {
    throw new Error("Dữ liệu Command Center không hợp lệ");
  }
  return body;
}

/** Lọc theo một dự án. `null` nghĩa là toàn bộ dự án. Trả về bản mới, không sửa dữ liệu gốc. */
export function filterByProject(
  data: CommandCenterData,
  projectCode: string | null,
): CommandCenterData {
  if (projectCode === null) {
    return data;
  }
  return {
    ...data,
    projects: data.projects.filter((row) => row.code === projectCode),
    red_alerts: data.red_alerts.filter((row) => row.project_code === projectCode),
    contract_countdowns: data.contract_countdowns.filter(
      (row) => row.project_code === projectCode,
    ),
  };
}

/** Định dạng số tiền (chuỗi thập phân từ API) theo tỷ đồng, kiểu vi-VN. */
export function formatBillionVnd(amount: string): string {
  const billions = Number(amount) / BILLION_VND;
  return `${BILLION_FORMATTER.format(billions)} tỷ`;
}

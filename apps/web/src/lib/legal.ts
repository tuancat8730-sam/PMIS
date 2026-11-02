import { resolveApiUrl } from "./api";

export type LegalPhaseGroup =
  | "PREPARATION"
  | "BIDDING"
  | "CONTRACT_KICKOFF"
  | "IMPLEMENTATION"
  | "ACCEPTANCE";

export type LegalMaturityStatus =
  | "MISSING"
  | "DRAFT_DOCX"
  | "SUBMITTED_REVIEW"
  | "WAITING_SIGNATURE"
  | "SIGNED_SCAN_PDF"
  | "DISCREPANCY_FOUND"
  | "VERIFIED_CLOSED";

export interface LegalDocumentRow {
  id: string;
  project_id: string;
  stt: number | null;
  phase_group: LegalPhaseGroup;
  doc_code_symbol: string | null;
  doc_name: string;
  issuing_authority: string | null;
  issue_date: string | null;
  is_mandatory: boolean;
  maturity_status: LegalMaturityStatus;
  pm_action_required: string | null;
  assigned_to: string | null;
  due_date: string | null;
  notes: string | null;
}

export interface LegalPhaseGroupView {
  phase: LegalPhaseGroup;
  rows: LegalDocumentRow[];
}

const PHASE_ORDER: readonly LegalPhaseGroup[] = [
  "PREPARATION",
  "BIDDING",
  "CONTRACT_KICKOFF",
  "IMPLEMENTATION",
  "ACCEPTANCE",
];

const PHASE_LABELS: Record<LegalPhaseGroup, string> = {
  PREPARATION: "Chuẩn bị đầu tư",
  BIDDING: "Lựa chọn nhà thầu",
  CONTRACT_KICKOFF: "Ký kết hợp đồng",
  IMPLEMENTATION: "Thực hiện",
  ACCEPTANCE: "Nghiệm thu, thanh lý",
};

const STATUS_LABELS: Record<LegalMaturityStatus, string> = {
  MISSING: "Chưa có file",
  DRAFT_DOCX: "Bản thảo Word",
  SUBMITTED_REVIEW: "Đã trình xem xét",
  WAITING_SIGNATURE: "Chờ ký",
  SIGNED_SCAN_PDF: "Đã ký (bản scan)",
  DISCREPANCY_FOUND: "Có sai sót",
  VERIFIED_CLOSED: "Đã kiểm tra, đóng",
};

function isLegalDocumentList(value: unknown): value is LegalDocumentRow[] {
  return Array.isArray(value);
}

/** Tải toàn bộ hồ sơ pháp lý của dự án. Ném lỗi kèm mã HTTP khi không tải được. */
export async function fetchLegalDocuments(
  projectId: string,
  token: string,
  fetchImpl: typeof fetch = fetch,
  baseUrl: string | undefined = process.env.NEXT_PUBLIC_API_URL,
): Promise<LegalDocumentRow[]> {
  const path = `/api/v1/projects/${encodeURIComponent(projectId)}/legal-documents`;
  const response = await fetchImpl(resolveApiUrl(path, baseUrl), {
    cache: "no-store",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(`Không tải được hồ sơ pháp lý (mã ${response.status})`);
  }
  const body: unknown = await response.json();
  if (!isLegalDocumentList(body)) {
    throw new Error("Dữ liệu hồ sơ pháp lý không hợp lệ");
  }
  return body;
}

/** Nhóm theo giai đoạn theo thứ tự chuẩn; bỏ giai đoạn không có hồ sơ. Không sửa mảng đầu vào. */
export function groupLegalDocumentsByPhase(
  documents: readonly LegalDocumentRow[],
): LegalPhaseGroupView[] {
  return PHASE_ORDER.flatMap((phase) => {
    const rows = documents
      .filter((document) => document.phase_group === phase)
      .sort((left, right) => (left.stt ?? 0) - (right.stt ?? 0));
    return rows.length === 0 ? [] : [{ phase, rows }];
  });
}

export function legalPhaseLabel(phase: LegalPhaseGroup): string {
  return PHASE_LABELS[phase];
}

export function legalStatusLabel(status: LegalMaturityStatus): string {
  return STATUS_LABELS[status];
}

import type { LegalMaturityStatus } from "./legal";
import type { MilestoneDisplayStatus, RiskLevel } from "./tracking";

/**
 * Mức nghiêm trọng hiển thị. `neutral` là chưa đánh giá hoặc chưa bắt đầu;
 * `low` là ổn; `critical` là cần xử lý ngay.
 */
export type Tone = "neutral" | "low" | "medium" | "high" | "critical";

const RISK_LEVEL_TONES: Record<RiskLevel, Tone> = {
  LOW: "low",
  MEDIUM: "medium",
  HIGH: "high",
  VERY_HIGH: "critical",
};

const MILESTONE_STATUS_TONES: Record<MilestoneDisplayStatus, Tone> = {
  NOT_STARTED: "neutral",
  IN_PROGRESS: "neutral",
  COMPLETED: "low",
  AT_RISK: "high",
  OVERDUE: "critical",
};

const LEGAL_STATUS_TONES: Record<LegalMaturityStatus, Tone> = {
  MISSING: "high",
  DRAFT_DOCX: "medium",
  SUBMITTED_REVIEW: "medium",
  WAITING_SIGNATURE: "medium",
  SIGNED_SCAN_PDF: "low",
  DISCREPANCY_FOUND: "critical",
  VERIFIED_CLOSED: "low",
};

/** `null` là chưa đánh giá nên dùng tông trung tính, không suy đoán mức. */
export function riskLevelTone(level: RiskLevel | null): Tone {
  return level === null ? "neutral" : RISK_LEVEL_TONES[level];
}

export function milestoneStatusTone(status: MilestoneDisplayStatus): Tone {
  return MILESTONE_STATUS_TONES[status];
}

export function legalStatusTone(status: LegalMaturityStatus): Tone {
  return LEGAL_STATUS_TONES[status];
}

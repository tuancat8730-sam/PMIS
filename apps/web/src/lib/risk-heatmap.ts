import type { Tone } from "./tone";
import type { RiskLevel, RiskRow } from "./tracking";

export interface RiskHeatmapCell {
  impact: RiskLevel;
  likelihood: RiskLevel;
  rows: RiskRow[];
}

export interface RiskHeatmap {
  /** 16 ô của lưới 4x4, luôn đủ dù không có rủi ro nào. */
  cells: RiskHeatmapCell[];
  /** Rủi ro thiếu tác động hoặc khả năng; không đặt vào ô nào. */
  unassessed: RiskRow[];
}

/** Thứ tự tăng dần, dùng cho cả trục tác động lẫn trục khả năng. */
export const RISK_LEVEL_ORDER: readonly RiskLevel[] = ["LOW", "MEDIUM", "HIGH", "VERY_HIGH"];

/** Hạng của rủi ro chưa có điểm; nhỏ hơn mọi điểm thật nên luôn xếp cuối. */
const UNSCORED_RANK = -1;

/** Tích hạng tác động × hạng khả năng (1 đến 16) được xếp vào từng mức màu của ô. */
const LOW_CELL_MAX = 3;
const MEDIUM_CELL_MAX = 6;
const HIGH_CELL_MAX = 9;

function levelRank(level: RiskLevel): number {
  return RISK_LEVEL_ORDER.indexOf(level) + 1;
}

/** Màu của một ô lưới theo tích hạng tác động và khả năng. */
export function riskCellTone(impact: RiskLevel, likelihood: RiskLevel): Tone {
  const product = levelRank(impact) * levelRank(likelihood);
  if (product <= LOW_CELL_MAX) {
    return "low";
  }
  if (product <= MEDIUM_CELL_MAX) {
    return "medium";
  }
  if (product <= HIGH_CELL_MAX) {
    return "high";
  }
  return "critical";
}

/** Xếp rủi ro vào lưới tác động × khả năng. Không sửa mảng đầu vào. */
export function buildRiskHeatmap(risks: readonly RiskRow[]): RiskHeatmap {
  const cells = RISK_LEVEL_ORDER.flatMap((impact) =>
    RISK_LEVEL_ORDER.map(
      (likelihood): RiskHeatmapCell => ({
        impact,
        likelihood,
        rows: risks.filter((risk) => risk.impact === impact && risk.likelihood === likelihood),
      }),
    ),
  );
  const unassessed = risks.filter((risk) => risk.impact === null || risk.likelihood === null);
  return { cells, unassessed };
}

/** Sắp theo điểm giảm dần; rủi ro chưa có điểm xếp cuối. Trả về mảng mới. */
export function sortRisksByScore(risks: readonly RiskRow[]): RiskRow[] {
  return [...risks].sort(
    (left, right) => (right.score ?? UNSCORED_RANK) - (left.score ?? UNSCORED_RANK),
  );
}

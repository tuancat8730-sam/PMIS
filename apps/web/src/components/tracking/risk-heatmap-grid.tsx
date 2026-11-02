import { Fragment } from "react";

import {
  RISK_LEVEL_ORDER,
  riskCellTone,
  type RiskHeatmap,
  type RiskHeatmapCell,
} from "../../lib/risk-heatmap";
import { riskLevelLabel, type RiskLevel } from "../../lib/tracking";
import { TONE_CLASSES } from "./ui/tone-classes";

/** Tác động xếp từ cao xuống thấp để ô nặng nhất nằm ở góc trên bên phải. */
const IMPACT_TOP_DOWN: readonly RiskLevel[] = [...RISK_LEVEL_ORDER].reverse();

function HeatmapCell({ cell }: { cell: RiskHeatmapCell }) {
  const count = cell.rows.length;
  return (
    <span
      title={`Tác động ${riskLevelLabel(cell.impact)}, khả năng ${riskLevelLabel(cell.likelihood)}: ${count} rủi ro`}
      className={`flex min-h-11 items-center justify-center rounded-md text-sm font-semibold tabular-nums ${TONE_CLASSES[riskCellTone(cell.impact, cell.likelihood)]}`}
    >
      {count}
    </span>
  );
}

/** Lưới 4×4 tác động × khả năng, kèm số rủi ro chưa đánh giá bên dưới. */
export function RiskHeatmapGrid({ heatmap }: { heatmap: RiskHeatmap }) {
  return (
    <div className="flex flex-col gap-3">
      <p className="text-sm font-medium text-foreground">Ma trận tác động và khả năng</p>
      <div className="grid grid-cols-[4.5rem_repeat(4,minmax(0,1fr))] gap-1 text-xs">
        <span />
        {RISK_LEVEL_ORDER.map((likelihood) => (
          <span key={likelihood} className="text-center text-text-muted">
            {riskLevelLabel(likelihood)}
          </span>
        ))}
        {IMPACT_TOP_DOWN.map((impact) => (
          <Fragment key={impact}>
            <span className="flex items-center text-text-muted">{riskLevelLabel(impact)}</span>
            {RISK_LEVEL_ORDER.map((likelihood) => {
              const cell = heatmap.cells.find(
                (candidate) => candidate.impact === impact && candidate.likelihood === likelihood,
              );
              return cell === undefined ? null : <HeatmapCell key={likelihood} cell={cell} />;
            })}
          </Fragment>
        ))}
      </div>
      <p className="text-sm text-text-muted">
        Chưa đánh giá: {heatmap.unassessed.length} rủi ro
      </p>
    </div>
  );
}

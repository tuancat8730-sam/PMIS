import { buildRiskHeatmap, sortRisksByScore } from "../../lib/risk-heatmap";
import { formatDateVi, riskLevelLabel, type RiskLevel, type RiskRow } from "../../lib/tracking";
import { riskLevelTone } from "../../lib/tone";
import { RiskHeatmapGrid } from "./risk-heatmap-grid";
import { EmptyState } from "./ui/empty-state";
import { ExpandableItem } from "./ui/expandable-item";
import { Field } from "./ui/field";
import { StatCard } from "./ui/stat-card";
import { StatusChip } from "./ui/status-chip";

const HIGH_IMPACT_LEVELS: readonly RiskLevel[] = ["HIGH", "VERY_HIGH"];

function RiskSummary({ row }: { row: RiskRow }) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-mono text-sm font-medium text-primary">{row.code}</span>
        <StatusChip
          tone={riskLevelTone(row.impact)}
          label={`Tác động: ${riskLevelLabel(row.impact)}`}
        />
        <StatusChip
          tone={riskLevelTone(row.likelihood)}
          label={`Khả năng: ${riskLevelLabel(row.likelihood)}`}
        />
        <span className="text-sm text-text-muted">Điểm {row.score ?? "—"}</span>
      </div>
      <p className="font-medium text-foreground">{row.title}</p>
    </div>
  );
}

function RiskDetails({ row }: { row: RiskRow }) {
  return (
    <dl className="grid grid-cols-1 gap-3 rounded-md bg-surface-muted p-3 sm:grid-cols-2 lg:grid-cols-4">
      <Field label="Người phụ trách" value={row.owner} />
      <Field
        label="Hạn xử lý"
        value={row.due_date === null ? null : formatDateVi(row.due_date)}
      />
      <Field label="Đơn vị phối hợp" value={row.coordinating_units} />
      <Field label="Trạng thái" value={row.status} />
    </dl>
  );
}

export function RiskTable({ rows }: { rows: RiskRow[] }) {
  if (rows.length === 0) {
    return <EmptyState message="Chưa có rủi ro nào." />;
  }
  const heatmap = buildRiskHeatmap(rows);
  const highImpactCount = rows.filter(
    (row) => row.impact !== null && HIGH_IMPACT_LEVELS.includes(row.impact),
  ).length;
  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <StatCard label="Tổng rủi ro" value={String(rows.length)} />
        <StatCard label="Tác động cao trở lên" value={String(highImpactCount)} />
        <StatCard label="Chưa đánh giá" value={String(heatmap.unassessed.length)} />
      </div>
      <div className="flex flex-col gap-6 lg:grid lg:grid-cols-[minmax(0,22rem)_minmax(0,1fr)] lg:items-start lg:gap-8">
        <RiskHeatmapGrid heatmap={heatmap} />
        <ul className="flex flex-col">
          {sortRisksByScore(rows).map((row) => (
            <ExpandableItem
              key={row.id}
              summary={<RiskSummary row={row} />}
              details={<RiskDetails row={row} />}
            />
          ))}
        </ul>
      </div>
    </div>
  );
}

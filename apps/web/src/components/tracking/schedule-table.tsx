import { EmptyState } from "./ui/empty-state";
import { ExpandableItem } from "./ui/expandable-item";
import { Field } from "./ui/field";
import { ProgressBar } from "./ui/progress-bar";
import { StatusChip } from "./ui/status-chip";
import { milestoneStatusTone } from "../../lib/tone";
import { formatDateVi, milestoneStatusLabel, type ScheduleRow } from "../../lib/tracking";

function MilestoneSummary({ row }: { row: ScheduleRow }) {
  const progress = Number(row.progress_percent);
  return (
    <div className="flex flex-col gap-2 lg:grid lg:grid-cols-[4rem_minmax(0,1fr)_7rem_8rem_10rem] lg:items-center lg:gap-4">
      <span className="font-mono text-sm font-medium text-primary">{row.code}</span>
      <span className="font-medium text-foreground">{row.name}</span>
      <span className="text-sm text-text-muted">Hạn {formatDateVi(row.baseline_end)}</span>
      <span>
        <StatusChip
          tone={milestoneStatusTone(row.display_status)}
          label={milestoneStatusLabel(row.display_status)}
        />
      </span>
      <div className="flex items-center gap-2">
        <ProgressBar label={`Tiến độ ${row.code}`} percent={progress} />
        <span className="shrink-0 text-sm tabular-nums">{progress}%</span>
      </div>
    </div>
  );
}

function MilestoneDetails({ row }: { row: ScheduleRow }) {
  return (
    <dl className="grid grid-cols-1 gap-3 rounded-md bg-surface-muted p-3 sm:grid-cols-2 lg:grid-cols-4">
      <Field label="Sản phẩm bàn giao" value={row.deliverables} />
      <Field label="Điều kiện nghiệm thu" value={row.acceptance_conditions} />
      <Field label="Mốc TVGS" value={row.tvgs_checkpoint} />
      <Field label="Ghi chú PM" value={row.pm_comment} />
    </dl>
  );
}

export function ScheduleTable({ rows }: { rows: ScheduleRow[] }) {
  if (rows.length === 0) {
    return <EmptyState message="Chưa có mốc tiến độ." />;
  }
  return (
    <ul className="flex flex-col">
      {rows.map((row) => (
        <ExpandableItem
          key={row.id}
          summary={<MilestoneSummary row={row} />}
          details={<MilestoneDetails row={row} />}
        />
      ))}
    </ul>
  );
}

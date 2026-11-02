import { MilestoneEditForm } from "./milestone-edit-form";
import { NoteList } from "./note-list";
import { TaskList } from "./task-list";
import { useProjectAccess, type ProjectAccess } from "./use-project-access";
import { EmptyState } from "./ui/empty-state";
import { ExpandableItem } from "./ui/expandable-item";
import { Field } from "./ui/field";
import { ProgressBar } from "./ui/progress-bar";
import { StatusChip } from "./ui/status-chip";
import { canEditMilestoneFields, canWriteTasksAndNotes } from "../../lib/milestone-permissions";
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

function MilestoneReadOnlyFields({ row }: { row: ScheduleRow }) {
  return (
    <dl className="grid grid-cols-1 gap-3 rounded-md bg-surface-muted p-3 sm:grid-cols-2 lg:grid-cols-4">
      <Field label="Sản phẩm bàn giao" value={row.deliverables} />
      <Field label="Điều kiện nghiệm thu" value={row.acceptance_conditions} />
      <Field label="Mốc TVGS" value={row.tvgs_checkpoint} />
      <Field label="Ghi chú PM" value={row.pm_comment} />
    </dl>
  );
}

interface MilestoneDetailsProps {
  row: ScheduleRow;
  projectId: string;
  access: ProjectAccess;
  onChanged: () => void;
}

function MilestoneDetails({ row, projectId, access, onChanged }: MilestoneDetailsProps) {
  const { token, role } = access;
  if (token === null) {
    return <MilestoneReadOnlyFields row={row} />;
  }
  const canEdit = canEditMilestoneFields(role);
  const canWrite = canWriteTasksAndNotes(role);
  return (
    <div className="flex flex-col gap-4">
      <MilestoneReadOnlyFields row={row} />
      {canEdit && (
        <MilestoneEditForm projectId={projectId} token={token} row={row} onSaved={onChanged} />
      )}
      <TaskList
        projectId={projectId}
        milestoneId={row.id}
        token={token}
        tasks={row.tasks}
        canWrite={canWrite}
        onChanged={onChanged}
      />
      <NoteList
        projectId={projectId}
        milestoneId={row.id}
        token={token}
        notes={row.notes}
        canWrite={canWrite}
        onChanged={onChanged}
      />
    </div>
  );
}

interface ScheduleTableProps {
  rows: ScheduleRow[];
  projectId: string;
  onChanged: () => void;
}

export function ScheduleTable({ rows, projectId, onChanged }: ScheduleTableProps) {
  const access = useProjectAccess(projectId);
  if (rows.length === 0) {
    return <EmptyState message="Chưa có mốc tiến độ." />;
  }
  return (
    <ul className="flex flex-col">
      {rows.map((row) => (
        <ExpandableItem
          key={row.id}
          summary={<MilestoneSummary row={row} />}
          details={
            <MilestoneDetails row={row} projectId={projectId} access={access} onChanged={onChanged} />
          }
        />
      ))}
    </ul>
  );
}

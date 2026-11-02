"use client";

import { useState, type FormEvent } from "react";

import { updateMilestone } from "../../lib/milestone-api";
import {
  describeError,
  parseMilestoneEdit,
  type MilestoneStatus,
} from "../../lib/milestone-forms";
import type { ScheduleRow } from "../../lib/tracking";

interface MilestoneEditFormProps {
  projectId: string;
  token: string;
  row: ScheduleRow;
  onSaved: () => void;
}

const STATUS_OPTIONS: ReadonlyArray<{ value: MilestoneStatus; label: string }> = [
  { value: "NOT_STARTED", label: "Chưa bắt đầu" },
  { value: "IN_PROGRESS", label: "Đang thực hiện" },
  { value: "COMPLETED", label: "Hoàn thành" },
];

const FIELD_CLASS =
  "min-h-11 w-full rounded-md border border-border-subtle bg-surface px-3 text-sm text-foreground";

/** Form PM dùng để sửa hạn, ngày hoàn thành, % và trạng thái của mốc. */
export function MilestoneEditForm({ projectId, token, row, onSaved }: MilestoneEditFormProps) {
  const locked = row.status === "COMPLETED" || row.is_hard_deadline;
  const [adjustedEnd, setAdjustedEnd] = useState(row.adjusted_end ?? "");
  const [actualEnd, setActualEnd] = useState(row.actual_end ?? "");
  const [progressPercent, setProgressPercent] = useState(String(Number(row.progress_percent)));
  const [status, setStatus] = useState<MilestoneStatus>(row.status as MilestoneStatus);
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const parsed = parseMilestoneEdit(
      { adjustedEnd, actualEnd, progressPercent, status, reason },
      { locked, currentAdjustedEnd: row.adjusted_end },
    );
    if (!parsed.ok) {
      setError(parsed.message);
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await updateMilestone(projectId, row.id, parsed.value, token);
      onSaved();
    } catch (caught) {
      setError(describeError(caught));
    } finally {
      setSaving(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      aria-label={`Sửa mốc ${row.code}`}
      className="flex flex-col gap-3 rounded-md border border-border-subtle p-3"
    >
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <label className="flex flex-col gap-1 text-sm">
          Hạn điều chỉnh
          <input
            type="date"
            className={FIELD_CLASS}
            value={adjustedEnd}
            onChange={(event) => setAdjustedEnd(event.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Ngày hoàn thành thực tế
          <input
            type="date"
            className={FIELD_CLASS}
            value={actualEnd}
            onChange={(event) => setActualEnd(event.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          % hoàn thành
          <input
            type="number"
            min={0}
            max={100}
            step="any"
            className={FIELD_CLASS}
            value={progressPercent}
            onChange={(event) => setProgressPercent(event.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Trạng thái
          <select
            className={FIELD_CLASS}
            value={status}
            onChange={(event) => setStatus(event.target.value as MilestoneStatus)}
          >
            {STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </div>
      {locked && (
        <label className="flex flex-col gap-1 text-sm">
          Lý do đổi hạn (bắt buộc khi đổi hạn mốc đã khóa)
          <input
            type="text"
            className={FIELD_CLASS}
            value={reason}
            onChange={(event) => setReason(event.target.value)}
          />
        </label>
      )}
      {error !== null && (
        <p role="alert" className="text-sm text-red-700">
          {error}
        </p>
      )}
      <button
        type="submit"
        disabled={saving}
        className="min-h-11 self-start rounded-md bg-primary px-4 text-sm font-medium text-white disabled:opacity-60"
      >
        {saving ? "Đang lưu…" : "Lưu mốc"}
      </button>
    </form>
  );
}

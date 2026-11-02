import { z } from "zod";

export const MILESTONE_STATUSES = ["NOT_STARTED", "IN_PROGRESS", "COMPLETED"] as const;
export type MilestoneStatus = (typeof MILESTONE_STATUSES)[number];

export const TASK_STATUSES = MILESTONE_STATUSES;
export type TaskStatus = MilestoneStatus;

const PROGRESS_MIN = 0;
const PROGRESS_MAX = 100;
const PROGRESS_MESSAGE = `Phần trăm hoàn thành phải từ ${PROGRESS_MIN} đến ${PROGRESS_MAX}`;
const DATE_MESSAGE = "Ngày phải có dạng năm-tháng-ngày";
const DATE_PATTERN = /^\d{4}-\d{2}-\d{2}$/;
const REASON_MESSAGE = "Thay đổi hạn của mốc đã khóa cần ghi lý do";
const TASK_NAME_MESSAGE = "Tên task không được để trống";
const NO_TASK_LABEL = "Chưa có task con";

export type ParseResult<T> = { ok: true; value: T } | { ok: false; message: string };

export interface MilestoneEditInput {
  adjustedEnd: string;
  actualEnd: string;
  progressPercent: string;
  status: MilestoneStatus;
  reason: string;
}

export interface MilestoneEditContext {
  locked: boolean;
  currentAdjustedEnd: string | null;
}

export interface MilestoneUpdatePayload {
  adjusted_end: string | null;
  actual_end: string | null;
  progress_percent: number;
  status: MilestoneStatus;
  reason?: string;
}

export interface TaskFormInput {
  name: string;
  status: TaskStatus;
  assignee: string;
  dueDate: string;
  note: string;
}

export interface TaskPayload {
  name: string;
  status: TaskStatus;
  assignee: string | null;
  due_date: string | null;
  note: string | null;
}

const progressSchema = z
  .string()
  .trim()
  .regex(/^\d+(\.\d+)?$/, PROGRESS_MESSAGE)
  .transform(Number)
  .pipe(z.number().min(PROGRESS_MIN, PROGRESS_MESSAGE).max(PROGRESS_MAX, PROGRESS_MESSAGE));

const dateSchema = z.string().regex(DATE_PATTERN, DATE_MESSAGE);

function fail(message: string): { ok: false; message: string } {
  return { ok: false, message };
}

function parseOptionalDate(value: string): ParseResult<string | null> {
  const trimmed = value.trim();
  if (trimmed === "") {
    return { ok: true, value: null };
  }
  const parsed = dateSchema.safeParse(trimmed);
  return parsed.success ? { ok: true, value: parsed.data } : fail(DATE_MESSAGE);
}

function optionalText(value: string): string | null {
  const trimmed = value.trim();
  return trimmed === "" ? null : trimmed;
}

/**
 * Kiểm form sửa mốc. Đổi hạn của mốc đã khóa phải có lý do, khớp với quy tắc của server.
 */
export function parseMilestoneEdit(
  input: MilestoneEditInput,
  context: MilestoneEditContext,
): ParseResult<MilestoneUpdatePayload> {
  const progress = progressSchema.safeParse(input.progressPercent);
  if (!progress.success) {
    return fail(PROGRESS_MESSAGE);
  }
  const adjusted = parseOptionalDate(input.adjustedEnd);
  if (!adjusted.ok) {
    return adjusted;
  }
  const actual = parseOptionalDate(input.actualEnd);
  if (!actual.ok) {
    return actual;
  }

  const reason = input.reason.trim();
  const adjustedChanged = adjusted.value !== context.currentAdjustedEnd;
  if (context.locked && adjustedChanged && reason === "") {
    return fail(REASON_MESSAGE);
  }

  return {
    ok: true,
    value: {
      adjusted_end: adjusted.value,
      actual_end: actual.value,
      progress_percent: progress.data,
      status: input.status,
      ...(context.locked && adjustedChanged ? { reason } : {}),
    },
  };
}

export function parseTaskForm(input: TaskFormInput): ParseResult<TaskPayload> {
  const name = input.name.trim();
  if (name === "") {
    return fail(TASK_NAME_MESSAGE);
  }
  const dueDate = parseOptionalDate(input.dueDate);
  if (!dueDate.ok) {
    return dueDate;
  }
  return {
    ok: true,
    value: {
      name,
      status: input.status,
      assignee: optionalText(input.assignee),
      due_date: dueDate.value,
      note: optionalText(input.note),
    },
  };
}

const UNKNOWN_ERROR_MESSAGE = "Không lưu được thay đổi";

/** Thông điệp hiển thị cho người dùng; lỗi từ API đã là tiếng Việt. */
export function describeError(error: unknown): string {
  return error instanceof Error ? error.message : UNKNOWN_ERROR_MESSAGE;
}

/** "x/y task xong" để hiển thị ngay trên dòng mốc. */
export function taskProgressLabel(tasks: ReadonlyArray<{ status: string }>): string {
  if (tasks.length === 0) {
    return NO_TASK_LABEL;
  }
  const completed = tasks.filter((task) => task.status === "COMPLETED").length;
  return `${completed}/${tasks.length} task xong`;
}

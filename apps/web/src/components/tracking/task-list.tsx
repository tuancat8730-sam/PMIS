"use client";

import { useState, type FormEvent } from "react";

import { createTask, deleteTask, updateTask } from "../../lib/milestone-api";
import {
  TASK_STATUSES,
  describeError,
  parseTaskForm,
  taskProgressLabel,
  type TaskFormInput,
  type TaskStatus,
} from "../../lib/milestone-forms";
import type { TaskRow } from "../../lib/tracking";

interface TaskListProps {
  projectId: string;
  milestoneId: string;
  token: string;
  tasks: TaskRow[];
  canWrite: boolean;
  onChanged: () => void;
}

const TASK_STATUS_LABELS: Record<TaskStatus, string> = {
  NOT_STARTED: "Chưa bắt đầu",
  IN_PROGRESS: "Đang thực hiện",
  COMPLETED: "Hoàn thành",
};

const EMPTY_DRAFT: TaskFormInput = {
  name: "",
  status: "NOT_STARTED",
  assignee: "",
  dueDate: "",
  note: "",
};

const FIELD_CLASS =
  "min-h-11 w-full rounded-md border border-border-subtle bg-surface px-3 text-sm text-foreground";

/** Danh sách task con của một mốc: đổi trạng thái, xóa, và thêm mới khi có quyền. */
export function TaskList({ projectId, milestoneId, token, tasks, canWrite, onChanged }: TaskListProps) {
  const [draft, setDraft] = useState<TaskFormInput>(EMPTY_DRAFT);
  const [error, setError] = useState<string | null>(null);

  async function runWrite(action: () => Promise<void>) {
    setError(null);
    try {
      await action();
      onChanged();
    } catch (caught) {
      setError(describeError(caught));
    }
  }

  function handleAdd(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const parsed = parseTaskForm(draft);
    if (!parsed.ok) {
      setError(parsed.message);
      return;
    }
    void runWrite(async () => {
      await createTask(projectId, milestoneId, parsed.value, token);
      setDraft(EMPTY_DRAFT);
    });
  }

  return (
    <section aria-label="Task con" className="flex flex-col gap-3">
      <h3 className="text-sm font-semibold text-foreground">
        Task con · {taskProgressLabel(tasks)}
      </h3>
      {tasks.length > 0 && (
        <ul className="flex flex-col gap-2">
          {tasks.map((task) => (
            <li
              key={task.id}
              className="flex flex-col gap-2 rounded-md bg-surface-muted p-3 sm:flex-row sm:items-center"
            >
              <span className="min-w-0 flex-1 text-sm font-medium text-foreground">
                {task.name}
                {task.assignee !== null && (
                  <span className="block text-xs text-text-muted">Phụ trách: {task.assignee}</span>
                )}
                {task.due_date !== null && (
                  <span className="block text-xs text-text-muted">Hạn: {task.due_date}</span>
                )}
                {task.is_overdue && (
                  <span className="block text-xs font-semibold text-red-700">Trễ hạn</span>
                )}
              </span>
              <select
                aria-label={`Trạng thái task ${task.name}`}
                className={`${FIELD_CLASS} sm:w-44`}
                value={task.status}
                disabled={!canWrite}
                onChange={(event) =>
                  void runWrite(() =>
                    updateTask(projectId, milestoneId, task.id, {
                      status: event.target.value as TaskStatus,
                    }, token),
                  )
                }
              >
                {TASK_STATUSES.map((status) => (
                  <option key={status} value={status}>
                    {TASK_STATUS_LABELS[status]}
                  </option>
                ))}
              </select>
              {canWrite && (
                <button
                  type="button"
                  className="min-h-11 rounded-md border border-border-subtle px-3 text-sm text-red-700"
                  onClick={() =>
                    void runWrite(() => deleteTask(projectId, milestoneId, task.id, token))
                  }
                >
                  Xóa
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
      {canWrite && (
        <form onSubmit={handleAdd} aria-label="Thêm task con" className="flex flex-col gap-2">
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
            <input
              aria-label="Tên task"
              placeholder="Tên task"
              className={FIELD_CLASS}
              value={draft.name}
              onChange={(event) => setDraft({ ...draft, name: event.target.value })}
            />
            <input
              aria-label="Người phụ trách"
              placeholder="Người phụ trách"
              className={FIELD_CLASS}
              value={draft.assignee}
              onChange={(event) => setDraft({ ...draft, assignee: event.target.value })}
            />
            <input
              type="date"
              aria-label="Hạn hoàn thành task"
              className={FIELD_CLASS}
              value={draft.dueDate}
              onChange={(event) => setDraft({ ...draft, dueDate: event.target.value })}
            />
          </div>
          <input
            aria-label="Ghi chú task"
            placeholder="Ghi chú riêng của task"
            className={FIELD_CLASS}
            value={draft.note}
            onChange={(event) => setDraft({ ...draft, note: event.target.value })}
          />
          <button
            type="submit"
            className="min-h-11 self-start rounded-md border border-border-subtle px-4 text-sm font-medium text-primary"
          >
            Thêm task
          </button>
        </form>
      )}
      {error !== null && (
        <p role="alert" className="text-sm text-red-700">
          {error}
        </p>
      )}
    </section>
  );
}

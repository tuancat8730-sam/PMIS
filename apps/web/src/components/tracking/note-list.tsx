"use client";

import { useState, type FormEvent } from "react";

import { createNote } from "../../lib/milestone-api";
import { describeError } from "../../lib/milestone-forms";
import type { NoteRow } from "../../lib/tracking";

interface NoteListProps {
  projectId: string;
  milestoneId: string;
  token: string;
  notes: NoteRow[];
  canWrite: boolean;
  onChanged: () => void;
}

const EMPTY_NOTE_MESSAGE = "Ghi chú không được để trống";

function formatNoteTime(isoTimestamp: string): string {
  return new Date(isoTimestamp).toLocaleString("vi-VN");
}

/** Nhật ký ghi chú của mốc: chỉ thêm, không sửa, không xóa. Mới nhất hiện trước. */
export function NoteList({ projectId, milestoneId, token, notes, canWrite, onChanged }: NoteListProps) {
  const [body, setBody] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = body.trim();
    if (trimmed === "") {
      setError(EMPTY_NOTE_MESSAGE);
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await createNote(projectId, milestoneId, trimmed, token);
      setBody("");
      onChanged();
    } catch (caught) {
      setError(describeError(caught));
    } finally {
      setSaving(false);
    }
  }

  return (
    <section aria-label="Ghi chú" className="flex flex-col gap-3">
      <h3 className="text-sm font-semibold text-foreground">Ghi chú</h3>
      {notes.length === 0 && <p className="text-sm text-text-muted">Chưa có ghi chú.</p>}
      {notes.length > 0 && (
        <ul className="flex flex-col gap-2">
          {notes.map((note) => (
            <li key={note.id} className="rounded-md bg-surface-muted p-3">
              <p className="whitespace-pre-line text-sm text-foreground">{note.body}</p>
              <time dateTime={note.created_at} className="text-xs text-text-muted">
                {formatNoteTime(note.created_at)}
              </time>
            </li>
          ))}
        </ul>
      )}
      {canWrite && (
        <form onSubmit={handleSubmit} aria-label="Thêm ghi chú" className="flex flex-col gap-2">
          <textarea
            aria-label="Nội dung ghi chú"
            rows={3}
            maxLength={2000}
            className="w-full rounded-md border border-border-subtle bg-surface p-3 text-sm text-foreground"
            value={body}
            onChange={(event) => setBody(event.target.value)}
          />
          <button
            type="submit"
            disabled={saving}
            className="min-h-11 self-start rounded-md border border-border-subtle px-4 text-sm font-medium text-primary disabled:opacity-60"
          >
            {saving ? "Đang gửi…" : "Thêm ghi chú"}
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

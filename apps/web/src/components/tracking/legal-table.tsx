"use client";

import { useState } from "react";

import {
  filterLegalDocuments,
  groupLegalDocumentsByPhase,
  legalPhaseLabel,
  legalStatusLabel,
  legalStatusSummary,
  type LegalDocumentRow,
  type LegalFilter,
  type LegalPhaseGroupView,
} from "../../lib/legal";
import { formatDateVi } from "../../lib/tracking";
import { legalStatusTone } from "../../lib/tone";
import { EmptyState } from "./ui/empty-state";
import { ExpandableItem } from "./ui/expandable-item";
import { Field } from "./ui/field";
import { StatCard } from "./ui/stat-card";
import { StatusChip } from "./ui/status-chip";

const FILTER_OPTIONS: readonly { value: LegalFilter; label: string }[] = [
  { value: "ALL", label: "Tất cả" },
  { value: "MISSING", label: "Thiếu" },
  { value: "DISCREPANCY", label: "Có sai sót" },
  { value: "IN_PROGRESS", label: "Đang xử lý" },
  { value: "DONE", label: "Đã ký hoặc đóng" },
];

const NO_SOURCE_TEXT = "Chưa có nguồn";

function LegalSummary({ rows }: { rows: LegalDocumentRow[] }) {
  const summary = legalStatusSummary(rows);
  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      <StatCard label="Tổng hồ sơ" value={String(summary.total)} />
      <StatCard
        label="Đã ký hoặc đóng"
        value={String(summary.signed + summary.verifiedClosed)}
      />
      <StatCard label="Đang xử lý" value={String(summary.inProgress)} />
      <StatCard
        label="Thiếu bắt buộc"
        value={String(summary.mandatoryMissing)}
        hint={`Thiếu ${summary.missing}, có sai sót ${summary.discrepancy}`}
      />
    </div>
  );
}

function DocumentSummary({ row }: { row: LegalDocumentRow }) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-mono text-sm text-primary">STT {row.stt ?? "—"}</span>
        <StatusChip
          tone={legalStatusTone(row.maturity_status)}
          label={legalStatusLabel(row.maturity_status)}
        />
        {row.is_mandatory && (
          <span className="text-xs font-medium text-text-muted">Bắt buộc</span>
        )}
      </div>
      <p className="font-medium text-foreground">{row.doc_name}</p>
    </div>
  );
}

function DocumentDetails({ row }: { row: LegalDocumentRow }) {
  return (
    <dl className="grid grid-cols-1 gap-3 rounded-md bg-surface-muted p-3 sm:grid-cols-2 lg:grid-cols-4">
      <Field label="Số hiệu" value={row.doc_code_symbol} />
      <Field label="Đơn vị ban hành" value={row.issuing_authority} />
      <Field
        label="Ngày ban hành"
        value={row.issue_date === null ? null : formatDateVi(row.issue_date)}
      />
      <Field label="Người phụ trách" value={row.assigned_to} missingText={NO_SOURCE_TEXT} />
      <Field
        label="Hạn xử lý"
        value={row.due_date === null ? null : formatDateVi(row.due_date)}
      />
      <Field label="Hành động PM" value={row.pm_action_required} missingText={NO_SOURCE_TEXT} />
      <Field label="Ghi chú" value={row.notes} />
    </dl>
  );
}

/** Accordion theo giai đoạn. Chỉ giai đoạn đầu mở sẵn, các giai đoạn khác đóng. */
function PhaseSection({
  group,
  defaultOpen,
}: {
  group: LegalPhaseGroupView;
  defaultOpen: boolean;
}) {
  return (
    <details open={defaultOpen} className="rounded-lg border border-border-subtle">
      <summary className="flex min-h-11 cursor-pointer items-center justify-between gap-3 px-4 py-3 font-semibold text-primary">
        <span>{legalPhaseLabel(group.phase)}</span>
        <span className="text-sm font-normal text-text-muted">{group.rows.length} hồ sơ</span>
      </summary>
      <ul className="flex flex-col px-4">
        {group.rows.map((row) => (
          <ExpandableItem
            key={row.id}
            summary={<DocumentSummary row={row} />}
            details={<DocumentDetails row={row} />}
          />
        ))}
      </ul>
    </details>
  );
}

function FilterChips({
  selected,
  onSelect,
}: {
  selected: LegalFilter;
  onSelect: (filter: LegalFilter) => void;
}) {
  return (
    <div role="group" aria-label="Lọc theo tình trạng" className="flex flex-wrap gap-2">
      {FILTER_OPTIONS.map((option) => (
        <button
          key={option.value}
          type="button"
          aria-pressed={selected === option.value}
          onClick={() => onSelect(option.value)}
          className={`min-h-11 rounded-full border px-4 text-sm font-medium ${
            selected === option.value
              ? "border-primary bg-primary text-primary-foreground"
              : "border-border-subtle bg-background text-foreground hover:border-primary"
          }`}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

export function LegalTable({ rows }: { rows: LegalDocumentRow[] }) {
  const [filter, setFilter] = useState<LegalFilter>("ALL");
  if (rows.length === 0) {
    return <EmptyState message="Chưa có hồ sơ pháp lý nào." />;
  }
  const groups = groupLegalDocumentsByPhase(filterLegalDocuments(rows, filter));
  return (
    <div className="flex flex-col gap-6">
      <LegalSummary rows={rows} />
      <FilterChips selected={filter} onSelect={setFilter} />
      {groups.length === 0 ? (
        <EmptyState message="Không có hồ sơ nào khớp bộ lọc." />
      ) : (
        <div className="flex flex-col gap-3">
          {groups.map((group, index) => (
            <PhaseSection key={group.phase} group={group} defaultOpen={index === 0} />
          ))}
        </div>
      )}
    </div>
  );
}

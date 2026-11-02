import {
  groupFileRegisterByFolder,
  type FileRegisterFolderGroup,
  type FileRegisterRow,
} from "../../lib/file-register";
import { EmptyState } from "./ui/empty-state";
import { ExpandableItem } from "./ui/expandable-item";
import { Field } from "./ui/field";
import { StatusChip } from "./ui/status-chip";

const EMPTY_VALUE_TEXT = "—";
const NO_FOLDER_HEADING = "Chưa phân thư mục";

function FileSummary({ entry }: { entry: FileRegisterRow }) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-mono text-sm text-primary">STT {entry.stt}</span>
        <span className="rounded bg-surface-muted px-2 py-0.5 text-xs text-foreground">
          {entry.file_format ?? EMPTY_VALUE_TEXT}
        </span>
        {entry.legal_status !== null && (
          <StatusChip tone="neutral" label={entry.legal_status} />
        )}
      </div>
      <p className="break-all font-medium text-foreground">{entry.file_name}</p>
    </div>
  );
}

function FileDetails({ entry }: { entry: FileRegisterRow }) {
  return (
    <dl className="grid grid-cols-1 gap-3 rounded-md bg-surface-muted p-3 sm:grid-cols-2 lg:grid-cols-4">
      <Field label="Vị trí lưu" value={entry.storage_location} missingText={EMPTY_VALUE_TEXT} />
      <Field label="Mục đích" value={entry.purpose} missingText={EMPTY_VALUE_TEXT} />
      <Field
        label="Bảo mật / sở hữu"
        value={entry.security_ownership}
        missingText={EMPTY_VALUE_TEXT}
      />
      <Field
        label="Hành động tiếp theo"
        value={entry.next_action}
        missingText={EMPTY_VALUE_TEXT}
      />
    </dl>
  );
}

function FolderSection({ group }: { group: FileRegisterFolderGroup }) {
  return (
    <section className="flex flex-col gap-2">
      <h2 className="text-sm font-semibold text-primary">{group.folder ?? NO_FOLDER_HEADING}</h2>
      <ul className="flex flex-col rounded-lg border border-border-subtle px-4">
        {group.rows.map((entry) => (
          <ExpandableItem
            key={entry.id}
            summary={<FileSummary entry={entry} />}
            details={<FileDetails entry={entry} />}
          />
        ))}
      </ul>
    </section>
  );
}

export function FileRegisterTable({ rows }: { rows: FileRegisterRow[] }) {
  const groups = groupFileRegisterByFolder(rows);
  if (groups.length === 0) {
    return <EmptyState message="Chưa có file nào trong danh mục." />;
  }
  return (
    <div className="flex flex-col gap-6">
      {groups.map((group) => (
        <FolderSection key={group.folder ?? NO_FOLDER_HEADING} group={group} />
      ))}
    </div>
  );
}

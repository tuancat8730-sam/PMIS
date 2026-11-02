import { formatFileSize, type DriveFileRow, type DriveFolderGroup } from "../../lib/drive-files";

interface DriveFileGroupsProps {
  groups: readonly DriveFolderGroup[];
  onOpen: (file: DriveFileRow) => void;
}

const MODIFIED_DATE_FORMAT: Intl.DateTimeFormatOptions = {
  dateStyle: "short",
  timeZone: "Asia/Ho_Chi_Minh",
};

const ROOT_FOLDER_LABEL = "Thư mục gốc";

function folderLabel(folder: string | null): string {
  return folder ?? ROOT_FOLDER_LABEL;
}

function formatModifiedDate(iso: string | null): string {
  if (iso === null) {
    return "—";
  }
  return new Date(iso).toLocaleDateString("vi-VN", MODIFIED_DATE_FORMAT);
}

/** Danh sách file theo từng thư mục. Chỉ hiển thị, không tải dữ liệu. */
export function DriveFileGroups({ groups, onOpen }: DriveFileGroupsProps) {
  return (
    <div className="flex flex-col gap-5">
      {groups.map((group) => (
        <section
          key={group.folder ?? ROOT_FOLDER_LABEL}
          aria-label={folderLabel(group.folder)}
          className="flex flex-col gap-2"
        >
          <h2 className="text-sm font-semibold text-neutral-600">{folderLabel(group.folder)}</h2>
          <ul className="flex flex-col divide-y divide-neutral-200 rounded-md border border-neutral-200 bg-white">
            {group.files.map((file) => (
              <li key={file.id} className="flex items-center justify-between gap-3 px-3 py-2">
                <div className="min-w-0">
                  <p className="truncate font-medium text-neutral-900">{file.file_name}</p>
                  <p className="text-xs text-neutral-500">
                    {formatFileSize(file.file_size)} · sửa {formatModifiedDate(file.modified_time)}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => onOpen(file)}
                  className="min-h-11 min-w-11 shrink-0 rounded-md border border-neutral-300 px-3 font-semibold text-neutral-900"
                >
                  Xem
                </button>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}

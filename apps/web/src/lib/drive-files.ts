import { resolveApiUrl } from "./api";

export interface DriveFileRow {
  id: string;
  drive_file_id: string;
  drive_path: string | null;
  file_name: string;
  mime_type: string | null;
  file_size: number | null;
  web_view_link: string | null;
  modified_time: string | null;
  last_synced_at: string;
}

export interface DriveSyncCounts {
  scanned: number;
  created: number;
  updated: number;
  removed: number;
}

export type DriveKind = "PDF" | "DOCX" | "XLSX" | "IMAGE" | "AUDIO";
export type DriveKindFilter = "ALL" | DriveKind;

export interface DriveFolderGroup {
  folder: string | null;
  files: DriveFileRow[];
}

const KIND_BY_EXTENSION: Readonly<Record<string, DriveKind>> = {
  pdf: "PDF",
  docx: "DOCX",
  xlsx: "XLSX",
  jpg: "IMAGE",
  jpeg: "IMAGE",
  m4a: "AUDIO",
};

const SYNC_ERROR_MESSAGES: Readonly<Record<number, string>> = {
  403: "Chỉ PM của dự án mới được quét ngay",
  409: "Dự án chưa khai báo thư mục gốc trên Google Drive",
  502: "Google Drive đang từ chối yêu cầu, hãy thử lại sau",
  503: "Máy chủ chưa cấu hình tài khoản dịch vụ Google Drive",
};

const KIB = 1024;
const MIB = KIB * KIB;
const VIETNAMESE_COLLATOR = new Intl.Collator("vi");

function isDriveFileList(value: unknown): value is DriveFileRow[] {
  return Array.isArray(value);
}

function isDriveSyncCounts(value: unknown): value is DriveSyncCounts {
  return (
    typeof value === "object" &&
    value !== null &&
    "scanned" in value &&
    "created" in value &&
    "updated" in value &&
    "removed" in value
  );
}

/** Phân loại theo đuôi file, giống quy tắc phía API. Trả về null nếu không xem và không đồng bộ. */
export function driveFileKind(fileName: string): DriveKind | null {
  const dotIndex = fileName.lastIndexOf(".");
  if (dotIndex === -1) {
    return null;
  }
  const kind: DriveKind | undefined = KIND_BY_EXTENSION[fileName.slice(dotIndex + 1).toLowerCase()];
  return kind ?? null;
}

/** Tải danh sách file Drive đang có của dự án. Ném lỗi kèm mã HTTP khi không tải được. */
export async function fetchDriveFiles(
  projectId: string,
  token: string,
  fetchImpl: typeof fetch = fetch,
  baseUrl: string | undefined = process.env.NEXT_PUBLIC_API_URL,
): Promise<DriveFileRow[]> {
  const path = `/api/v1/projects/${encodeURIComponent(projectId)}/drive/files`;
  const response = await fetchImpl(resolveApiUrl(path, baseUrl), {
    cache: "no-store",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(`Không tải được danh sách file Drive (mã ${response.status})`);
  }
  const body: unknown = await response.json();
  if (!isDriveFileList(body)) {
    throw new Error("Dữ liệu file Drive không hợp lệ");
  }
  return body;
}

/** Yêu cầu máy chủ quét Drive ngay. Lỗi được đổi sang thông điệp tiếng Việt theo mã HTTP. */
export async function triggerDriveSync(
  projectId: string,
  token: string,
  fetchImpl: typeof fetch = fetch,
  baseUrl: string | undefined = process.env.NEXT_PUBLIC_API_URL,
): Promise<DriveSyncCounts> {
  const path = `/api/v1/projects/${encodeURIComponent(projectId)}/drive/sync`;
  const response = await fetchImpl(resolveApiUrl(path, baseUrl), {
    method: "POST",
    cache: "no-store",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(
      SYNC_ERROR_MESSAGES[response.status] ?? `Không quét được Google Drive (mã ${response.status})`,
    );
  }
  const body: unknown = await response.json();
  if (!isDriveSyncCounts(body)) {
    throw new Error("Kết quả quét Google Drive không hợp lệ");
  }
  return body;
}

/** Nhóm file theo thư mục. Thư mục gốc là `folder: null` và luôn đứng đầu. Không sửa mảng đầu vào. */
export function groupDriveFilesByFolder(files: readonly DriveFileRow[]): DriveFolderGroup[] {
  const filesByFolder = new Map<string | null, DriveFileRow[]>();
  for (const file of [...files].sort((left, right) =>
    VIETNAMESE_COLLATOR.compare(left.file_name, right.file_name),
  )) {
    const folder = folderOf(file);
    filesByFolder.set(folder, [...(filesByFolder.get(folder) ?? []), file]);
  }
  return [...filesByFolder]
    .map(([folder, groupFiles]) => ({ folder, files: groupFiles }))
    .sort((left, right) => compareFolders(left.folder, right.folder));
}

/** Lọc theo tên (không phân biệt hoa thường) và theo loại file. Không sửa mảng đầu vào. */
export function filterDriveFiles(
  files: readonly DriveFileRow[],
  query: string,
  kind: DriveKindFilter,
): DriveFileRow[] {
  const normalizedQuery = query.trim().toLowerCase();
  return files.filter(
    (file) =>
      file.file_name.toLowerCase().includes(normalizedQuery) &&
      (kind === "ALL" || driveFileKind(file.file_name) === kind),
  );
}

/** Định dạng cỡ file theo kiểu Việt Nam (dấu phẩy thập phân). */
export function formatFileSize(bytes: number | null): string {
  if (bytes === null) {
    return "—";
  }
  if (bytes < KIB) {
    return `${bytes} B`;
  }
  if (bytes < MIB) {
    return `${formatDecimal(bytes / KIB)} KB`;
  }
  return `${formatDecimal(bytes / MIB)} MB`;
}

/** Thời điểm đồng bộ gần nhất trong danh sách, hoặc null khi chưa có file nào. */
export function latestSyncedAt(files: readonly DriveFileRow[]): string | null {
  if (files.length === 0) {
    return null;
  }
  return files.reduce(
    (latest, file) =>
      Date.parse(file.last_synced_at) > Date.parse(latest) ? file.last_synced_at : latest,
    files[0].last_synced_at,
  );
}

function folderOf(file: DriveFileRow): string | null {
  const path = file.drive_path ?? file.file_name;
  const separatorIndex = path.lastIndexOf("/");
  return separatorIndex === -1 ? null : path.slice(0, separatorIndex);
}

function compareFolders(left: string | null, right: string | null): number {
  if (left === null || right === null) {
    return left === right ? 0 : left === null ? -1 : 1;
  }
  return VIETNAMESE_COLLATOR.compare(left, right);
}

function formatDecimal(value: number): string {
  return value.toLocaleString("vi-VN", { maximumFractionDigits: 1 });
}

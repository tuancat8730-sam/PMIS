import { resolveApiUrl } from "./api";

export interface FileRegisterRow {
  id: string;
  project_id: string;
  stt: number;
  folder_path: string | null;
  file_name: string;
  file_format: string | null;
  storage_location: string | null;
  purpose: string | null;
  legal_status: string | null;
  security_ownership: string | null;
  next_action: string | null;
  drive_file_id: string | null;
}

function isFileRegisterList(value: unknown): value is FileRegisterRow[] {
  return Array.isArray(value);
}

/** Tải toàn bộ danh mục file và bằng chứng của dự án. Ném lỗi kèm mã HTTP khi không tải được. */
export async function fetchFileRegister(
  projectId: string,
  token: string,
  fetchImpl: typeof fetch = fetch,
  baseUrl: string | undefined = process.env.NEXT_PUBLIC_API_URL,
): Promise<FileRegisterRow[]> {
  const path = `/api/v1/projects/${encodeURIComponent(projectId)}/file-register`;
  const response = await fetchImpl(resolveApiUrl(path, baseUrl), {
    cache: "no-store",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(`Không tải được danh mục file (mã ${response.status})`);
  }
  const body: unknown = await response.json();
  if (!isFileRegisterList(body)) {
    throw new Error("Dữ liệu danh mục file không hợp lệ");
  }
  return body;
}

/** Sắp theo `stt` trên một bản sao; không sửa mảng đầu vào. */
export function sortFileRegister(entries: readonly FileRegisterRow[]): FileRegisterRow[] {
  return [...entries].sort((left, right) => left.stt - right.stt);
}

export interface FileRegisterFolderGroup {
  folder: string | null;
  rows: FileRegisterRow[];
}

/** Nhóm theo thư mục; nhóm xếp theo `stt` nhỏ nhất của nó, bên trong xếp theo `stt`. Không sửa mảng đầu vào. */
export function groupFileRegisterByFolder(
  entries: readonly FileRegisterRow[],
): FileRegisterFolderGroup[] {
  const rowsByFolder = new Map<string | null, FileRegisterRow[]>();
  for (const entry of sortFileRegister(entries)) {
    const rows = rowsByFolder.get(entry.folder_path) ?? [];
    rowsByFolder.set(entry.folder_path, [...rows, entry]);
  }
  return [...rowsByFolder].map(([folder, rows]) => ({ folder, rows }));
}

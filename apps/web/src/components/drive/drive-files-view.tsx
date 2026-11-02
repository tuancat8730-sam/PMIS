"use client";

import { useEffect, useMemo, useState } from "react";

import {
  fetchDriveFiles,
  filterDriveFiles,
  groupDriveFilesByFolder,
  latestSyncedAt,
  triggerDriveSync,
  type DriveFileRow,
  type DriveKindFilter,
} from "../../lib/drive-files";
import { readStoredToken } from "../tracking/matrix-page";
import { DriveFileGroups } from "./drive-file-groups";
import { DriveSyncBar } from "./drive-sync-bar";

interface DriveFilesViewProps {
  projectId: string;
}

const NO_SESSION_MESSAGE = "Chưa có phiên đăng nhập. Hãy đăng nhập lại.";
const KIND_OPTIONS: readonly { value: DriveKindFilter; label: string }[] = [
  { value: "ALL", label: "Tất cả loại" },
  { value: "PDF", label: "PDF" },
  { value: "DOCX", label: "Word (DOCX)" },
  { value: "XLSX", label: "Excel (XLSX)" },
  { value: "IMAGE", label: "Ảnh" },
  { value: "AUDIO", label: "Âm thanh" },
];

function errorText(error: unknown): string {
  return error instanceof Error ? error.message : "Không tải được dữ liệu";
}

function syncSummary(counts: { scanned: number; created: number; updated: number; removed: number }): string {
  return `Đã quét ${counts.scanned} file: thêm ${counts.created}, cập nhật ${counts.updated}, gỡ ${counts.removed}`;
}

/** Trang Tệp Drive của một dự án: tải danh sách, quét ngay, lọc và nhóm theo thư mục. */
export function DriveFilesView({ projectId }: DriveFilesViewProps) {
  const [files, setFiles] = useState<DriveFileRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [kind, setKind] = useState<DriveKindFilter>("ALL");
  const [syncing, setSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const token = readStoredToken();
    if (token === null) {
      setError(NO_SESSION_MESSAGE);
      return;
    }
    let cancelled = false;
    fetchDriveFiles(projectId, token)
      .then((data) => {
        if (!cancelled) {
          setFiles(data);
          setError(null);
        }
      })
      .catch((failure: unknown) => {
        if (!cancelled) {
          setError(errorText(failure));
        }
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, reloadKey]);

  useEffect(() => {
    const reloadOnFocus = () => setReloadKey((key) => key + 1);
    window.addEventListener("focus", reloadOnFocus);
    return () => window.removeEventListener("focus", reloadOnFocus);
  }, []);

  const visibleGroups = useMemo(
    () => groupDriveFilesByFolder(filterDriveFiles(files ?? [], query, kind)),
    [files, query, kind],
  );

  async function handleSync() {
    const token = readStoredToken();
    if (token === null) {
      setSyncMessage(NO_SESSION_MESSAGE);
      return;
    }
    setSyncing(true);
    setSyncMessage(null);
    try {
      const counts = await triggerDriveSync(projectId, token);
      setSyncMessage(syncSummary(counts));
      setReloadKey((key) => key + 1);
    } catch (failure: unknown) {
      setSyncMessage(errorText(failure));
    } finally {
      setSyncing(false);
    }
  }

  function handleOpen(file: DriveFileRow) {
    window.open(file.web_view_link ?? undefined, "_blank", "noopener,noreferrer");
  }

  return (
    <section className="flex flex-col gap-4">
      <DriveSyncBar
        lastSyncedAt={latestSyncedAt(files ?? [])}
        syncing={syncing}
        message={syncMessage}
        onSync={handleSync}
      />
      <div className="flex flex-wrap gap-2">
        <input
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Tìm theo tên file"
          className="min-h-11 min-w-0 flex-1 rounded-md border border-neutral-300 px-3"
        />
        <select
          value={kind}
          onChange={(event) => setKind(event.target.value as DriveKindFilter)}
          className="min-h-11 rounded-md border border-neutral-300 px-3"
        >
          {KIND_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
      {error && <p className="text-red-700">{error}</p>}
      {files === null && error === null && <p className="text-neutral-500">Đang tải…</p>}
      {files !== null && files.length === 0 && (
        <p className="text-neutral-700">Chưa có file nào trên Google Drive của dự án này.</p>
      )}
      {files !== null && files.length > 0 && visibleGroups.length === 0 && (
        <p className="text-neutral-700">Không có file khớp bộ lọc.</p>
      )}
      <DriveFileGroups groups={visibleGroups} onOpen={handleOpen} />
    </section>
  );
}

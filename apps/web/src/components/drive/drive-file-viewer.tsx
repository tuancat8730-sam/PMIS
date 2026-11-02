"use client";

import { useEffect, useState } from "react";

import {
  driveFileKind,
  fetchDriveFileBlob,
  type DriveFileRow,
} from "../../lib/drive-files";
import { readStoredToken } from "../tracking/matrix-page";

interface DriveFileViewerProps {
  projectId: string;
  file: DriveFileRow;
  onClose: () => void;
}

/** Thời gian giữ object URL sau khi tải về, để trình duyệt kịp bắt đầu ghi file. */
const DOWNLOAD_URL_RELEASE_MS = 1000;
const NO_SESSION_MESSAGE = "Chưa có phiên đăng nhập. Hãy đăng nhập lại.";
const NOT_PREVIEWABLE_MESSAGE = "Loại file này không xem trực tiếp được. Hãy tải về để mở.";

function errorText(error: unknown): string {
  return error instanceof Error ? error.message : "Không tải được file";
}

/** Xem trực tiếp PDF và ảnh trong dialog. Nội dung lấy qua API kèm token, không dùng link Drive. */
export function DriveFileViewer({ projectId, file, onClose }: DriveFileViewerProps) {
  const kind = driveFileKind(file.file_name);
  const previewable = kind === "PDF" || kind === "IMAGE";
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    if (!previewable) {
      return;
    }
    const token = readStoredToken();
    if (token === null) {
      setError(NO_SESSION_MESSAGE);
      return;
    }
    let cancelled = false;
    let objectUrl: string | null = null;
    fetchDriveFileBlob(projectId, file.drive_file_id, token, { download: false })
      .then((blob) => {
        if (cancelled) {
          return;
        }
        objectUrl = URL.createObjectURL(blob);
        setPreviewUrl(objectUrl);
      })
      .catch((failure: unknown) => {
        if (!cancelled) {
          setError(errorText(failure));
        }
      });
    return () => {
      cancelled = true;
      if (objectUrl !== null) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [projectId, file.drive_file_id, previewable]);

  async function handleDownload() {
    const token = readStoredToken();
    if (token === null) {
      setError(NO_SESSION_MESSAGE);
      return;
    }
    setDownloading(true);
    setError(null);
    try {
      const blob = await fetchDriveFileBlob(projectId, file.drive_file_id, token, { download: true });
      const objectUrl = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = objectUrl;
      link.download = file.file_name;
      link.click();
      setTimeout(() => URL.revokeObjectURL(objectUrl), DOWNLOAD_URL_RELEASE_MS);
    } catch (failure: unknown) {
      setError(errorText(failure));
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="drive-viewer-title"
      className="fixed inset-0 z-50 flex flex-col bg-white"
    >
      <header className="flex items-center justify-between gap-3 border-b border-neutral-200 p-3">
        <h2 id="drive-viewer-title" className="min-w-0 truncate font-semibold text-neutral-900">
          {file.file_name}
        </h2>
        <button
          type="button"
          onClick={onClose}
          className="min-h-11 min-w-11 shrink-0 rounded-md border border-neutral-300 px-3 font-semibold"
        >
          Đóng
        </button>
      </header>
      <div className="flex min-h-0 flex-1 items-center justify-center overflow-auto p-2">
        {!previewable && <p className="text-center text-neutral-700">{NOT_PREVIEWABLE_MESSAGE}</p>}
        {previewable && previewUrl === null && error === null && (
          <p className="text-neutral-500">Đang tải…</p>
        )}
        {previewable && previewUrl !== null && kind === "PDF" && (
          <iframe title={file.file_name} src={previewUrl} className="h-full w-full" />
        )}
        {previewable && previewUrl !== null && kind === "IMAGE" && (
          // eslint-disable-next-line @next/next/no-img-element -- blob URL, không qua bộ tối ưu ảnh của Next
          <img src={previewUrl} alt={file.file_name} className="max-h-full max-w-full object-contain" />
        )}
      </div>
      <footer className="flex flex-col gap-2 border-t border-neutral-200 p-3">
        {error && (
          <p role="alert" className="text-sm text-red-700">
            {error}
          </p>
        )}
        <button
          type="button"
          onClick={handleDownload}
          disabled={downloading}
          className={`min-h-11 rounded-md bg-neutral-900 px-4 font-semibold text-white${downloading ? " opacity-50" : ""}`}
        >
          {downloading ? "Đang tải…" : "Tải về"}
        </button>
      </footer>
    </div>
  );
}

"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { DEFAULT_API_URL } from "@/lib/api";
import { getOrCreateDeviceId } from "@/lib/device-id";
import { createFieldQueue, type FlushResult } from "@/lib/field-queue";
import { createIndexedDbStore } from "@/lib/field-queue-store";
import { createHttpSender } from "@/lib/field-sender";

export const TOKEN_STORAGE_KEY = "pmis.field.token";

export interface HandoverRow {
  readonly id: string;
  readonly cluster_code: string;
  readonly batch_code: string;
  readonly delivery_status: string;
  readonly version: number;
}

export const STATUS_CHOICES: ReadonlyArray<{ readonly value: string; readonly label: string }> = [
  { value: "IN_TRANSIT", label: "Đang vận chuyển" },
  { value: "INSTALLED", label: "Đã lắp đặt" },
  { value: "ISSUE_REPORTED", label: "Báo lỗi" },
];

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? DEFAULT_API_URL;

function readToken(): string | null {
  try {
    return sessionStorage.getItem(TOKEN_STORAGE_KEY);
  } catch {
    return null;
  }
}

function buildQueue() {
  return createFieldQueue({
    store: createIndexedDbStore(),
    send: createHttpSender({ baseUrl: API_BASE_URL, getToken: readToken }),
  });
}

async function fetchHandovers(projectId: string, token: string): Promise<HandoverRow[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/projects/${projectId}/delivery-handovers`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Không tải được danh sách (HTTP ${response.status})`);
  }
  return (await response.json()) as HandoverRow[];
}

function summarize(result: FlushResult): string {
  if (result.conflicted > 0) {
    return `${result.conflicted} thao tác bị xung đột, cần kiểm tra lại`;
  }
  if (result.sent > 0) {
    return `Đã gửi ${result.sent} thao tác`;
  }
  return "";
}

export function FieldWorkspace({ projectId }: { readonly projectId: string }) {
  const queue = useMemo(() => buildQueue(), []);
  const [deviceId, setDeviceId] = useState<string>("");
  const [rows, setRows] = useState<HandoverRow[]>([]);
  const [selected, setSelected] = useState<HandoverRow | null>(null);
  const [pendingCount, setPendingCount] = useState(0);
  const [notice, setNotice] = useState("");
  const [token, setToken] = useState<string | null>(null);

  const refreshPending = useCallback(async () => {
    setPendingCount((await queue.listPending()).length);
  }, [queue]);

  const flush = useCallback(async () => {
    const result = await queue.flush();
    setNotice(summarize(result));
    await refreshPending();
  }, [queue, refreshPending]);

  useEffect(() => {
    setDeviceId(getOrCreateDeviceId());
    setToken(readToken());
    void refreshPending();
    if ("serviceWorker" in navigator) {
      void navigator.serviceWorker.register("/sw.js");
    }
    window.addEventListener("online", flush);
    return () => window.removeEventListener("online", flush);
  }, [flush, refreshPending]);

  useEffect(() => {
    if (token === null) {
      return;
    }
    fetchHandovers(projectId, token)
      .then(setRows)
      .catch((error: unknown) => {
        setNotice(error instanceof Error ? error.message : "Không tải được danh sách");
      });
  }, [projectId, token]);

  async function chooseStatus(value: string): Promise<void> {
    if (selected === null) {
      return;
    }
    await queue.enqueue({
      deviceId,
      method: "PATCH",
      path: `/api/v1/projects/${projectId}/field/delivery-handovers/${selected.id}/status`,
      body: { delivery_status: value, expected_version: selected.version },
    });
    setSelected(null);
    setNotice("Đã lưu trên máy, sẽ gửi khi có mạng");
    await refreshPending();
    await flush();
  }

  if (token === null) {
    return <TokenForm onSave={(value) => setToken(value)} />;
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col gap-4 p-4">
      <header className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Hiện trường</h1>
        <span className="text-sm" aria-live="polite">
          Chờ gửi: {pendingCount}
        </span>
      </header>
      {notice !== "" && (
        <p role="status" className="rounded bg-slate-100 p-3 text-sm">
          {notice}
        </p>
      )}
      {selected === null ? (
        <HandoverList rows={rows} onPick={setSelected} />
      ) : (
        <StatusPicker row={selected} onChoose={chooseStatus} onBack={() => setSelected(null)} />
      )}
    </main>
  );
}

function HandoverList({
  rows,
  onPick,
}: {
  readonly rows: HandoverRow[];
  readonly onPick: (row: HandoverRow) => void;
}) {
  if (rows.length === 0) {
    return <p className="text-sm">Chưa có dòng giao hàng nào.</p>;
  }
  return (
    <ul className="flex flex-col gap-2">
      {rows.map((row) => (
        <li key={row.id}>
          <button
            type="button"
            onClick={() => onPick(row)}
            className="flex min-h-14 w-full items-center justify-between rounded border p-3 text-left"
          >
            <span>
              Cụm {row.cluster_code} · {row.batch_code}
            </span>
            <span className="text-sm">{row.delivery_status}</span>
          </button>
        </li>
      ))}
    </ul>
  );
}

function StatusPicker({
  row,
  onChoose,
  onBack,
}: {
  readonly row: HandoverRow;
  readonly onChoose: (value: string) => Promise<void>;
  readonly onBack: () => void;
}) {
  return (
    <section className="flex flex-col gap-3">
      <p className="text-sm">
        Cụm {row.cluster_code} · {row.batch_code}
      </p>
      {STATUS_CHOICES.map((choice) => (
        <button
          key={choice.value}
          type="button"
          onClick={() => void onChoose(choice.value)}
          className="min-h-14 rounded bg-sky-700 p-3 text-white"
        >
          {choice.label}
        </button>
      ))}
      <button type="button" onClick={onBack} className="min-h-14 rounded border p-3">
        Quay lại
      </button>
    </section>
  );
}

function TokenForm({ onSave }: { readonly onSave: (value: string) => void }) {
  const [value, setValue] = useState("");
  // Tạm thời: chưa có màn hình đăng nhập trên web. Token chỉ giữ trong phiên trình duyệt.
  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col gap-4 p-4">
      <h1 className="text-xl font-semibold">Đăng nhập thiết bị</h1>
      <label className="flex flex-col gap-2 text-sm">
        Mã truy cập
        <input
          value={value}
          onChange={(event) => setValue(event.target.value)}
          className="min-h-14 rounded border p-3"
        />
      </label>
      <button
        type="button"
        disabled={value.trim() === ""}
        onClick={() => {
          try {
            sessionStorage.setItem(TOKEN_STORAGE_KEY, value.trim());
          } catch {
            // Không lưu được vẫn dùng trong bộ nhớ của trang này.
          }
          onSave(value.trim());
        }}
        className="min-h-14 rounded bg-sky-700 p-3 text-white disabled:opacity-50"
      >
        Tiếp tục
      </button>
    </main>
  );
}

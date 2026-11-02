"use client";

import Link from "next/link";
import { useEffect, useState, type ReactNode } from "react";

import { SESSION_TOKEN_STORAGE_KEY } from "../../lib/command-center";

type LoadState<T> =
  | { kind: "loading" }
  | { kind: "no-token" }
  | { kind: "error"; message: string }
  | { kind: "ready"; data: T };

export function readStoredToken(): string | null {
  try {
    return window.localStorage.getItem(SESSION_TOKEN_STORAGE_KEY);
  } catch {
    return null;
  }
}

interface MatrixPageProps<T> {
  projectId: string;
  title: string;
  load: (token: string) => Promise<T>;
  render: (data: T) => ReactNode;
}

/** Khung chung cho các màn hình tracking: đọc token, tải dữ liệu, hiển thị lỗi hoặc nội dung. */
export function MatrixPage<T>({ projectId, title, load, render }: MatrixPageProps<T>) {
  const [state, setState] = useState<LoadState<T>>({ kind: "loading" });

  useEffect(() => {
    const token = readStoredToken();
    if (token === null) {
      setState({ kind: "no-token" });
      return;
    }
    load(token)
      .then((data) => setState({ kind: "ready", data }))
      .catch((error: unknown) =>
        setState({
          kind: "error",
          message: error instanceof Error ? error.message : "Không tải được dữ liệu",
        }),
      );
    // load được tạo lại mỗi lần render nhưng chỉ phụ thuộc projectId; chỉ tải khi đổi dự án.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  return (
    <main className="flex flex-col gap-4 p-6">
      <h1 className="text-xl font-semibold text-neutral-900">{title}</h1>
      {state.kind === "loading" && <p className="text-neutral-500">Đang tải…</p>}
      {state.kind === "no-token" && (
        <p className="text-neutral-700">
          Chưa có phiên đăng nhập.{" "}
          <Link href="/login" className="font-semibold underline underline-offset-4">
            Đăng nhập
          </Link>
        </p>
      )}
      {state.kind === "error" && <p className="text-red-700">{state.message}</p>}
      {state.kind === "ready" && render(state.data)}
    </main>
  );
}

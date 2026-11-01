"use client";

import { useEffect, useState } from "react";

import { CommandCenterView } from "@/components/command-center/command-center-view";
import {
  fetchCommandCenter,
  SESSION_TOKEN_STORAGE_KEY,
  type CommandCenterData,
} from "@/lib/command-center";

type LoadState =
  | { kind: "loading" }
  | { kind: "no-token" }
  | { kind: "error"; message: string }
  | { kind: "ready"; data: CommandCenterData };

function readStoredToken(): string | null {
  try {
    return window.localStorage.getItem(SESSION_TOKEN_STORAGE_KEY);
  } catch {
    return null;
  }
}

export default function CommandCenterPage() {
  const [state, setState] = useState<LoadState>({ kind: "loading" });
  const [selectedCode, setSelectedCode] = useState<string | null>(null);

  useEffect(() => {
    const token = readStoredToken();
    if (token === null) {
      setState({ kind: "no-token" });
      return;
    }
    fetchCommandCenter(token)
      .then((data) => setState({ kind: "ready", data }))
      .catch((error: unknown) =>
        setState({
          kind: "error",
          message: error instanceof Error ? error.message : "Không tải được dữ liệu",
        }),
      );
  }, []);

  if (state.kind === "loading") {
    return <p className="p-10 text-neutral-500">Đang tải Command Center…</p>;
  }
  if (state.kind === "no-token") {
    return (
      <p className="p-10 text-neutral-700">
        Chưa có phiên đăng nhập. Đăng nhập trước khi xem Command Center.
      </p>
    );
  }
  if (state.kind === "error") {
    return <p className="p-10 text-red-700">{state.message}</p>;
  }
  return (
    <CommandCenterView
      data={state.data}
      selectedCode={selectedCode}
      onSelectProject={setSelectedCode}
    />
  );
}

"use client";

import { useParams } from "next/navigation";

import { DriveFilesView } from "../../../../components/drive/drive-files-view";

export default function DriveFilesPage() {
  const { projectId } = useParams<{ projectId: string }>();
  return (
    <main className="flex flex-col gap-4 p-6">
      <h1 className="text-xl font-semibold text-neutral-900">Tệp Drive</h1>
      <DriveFilesView projectId={projectId} />
    </main>
  );
}

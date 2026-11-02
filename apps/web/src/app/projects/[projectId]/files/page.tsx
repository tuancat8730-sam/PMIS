"use client";

import { useParams } from "next/navigation";

import { FileRegisterTable } from "../../../../components/tracking/file-register-table";
import { MatrixPage } from "../../../../components/tracking/matrix-page";
import { fetchFileRegister } from "../../../../lib/file-register";

export default function FilesPage() {
  const { projectId } = useParams<{ projectId: string }>();
  return (
    <MatrixPage
      projectId={projectId}
      title="File & bằng chứng"
      load={(token) => fetchFileRegister(projectId, token)}
      render={(rows) => <FileRegisterTable rows={rows} />}
    />
  );
}

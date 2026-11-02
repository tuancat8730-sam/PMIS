"use client";

import { useParams } from "next/navigation";

import { LegalTable } from "../../../../components/tracking/legal-table";
import { MatrixPage } from "../../../../components/tracking/matrix-page";
import { fetchLegalDocuments } from "../../../../lib/legal";

export default function LegalPage() {
  const { projectId } = useParams<{ projectId: string }>();
  return (
    <MatrixPage
      projectId={projectId}
      title="Hồ sơ pháp lý"
      load={(token) => fetchLegalDocuments(projectId, token)}
      render={(rows) => <LegalTable rows={rows} />}
    />
  );
}

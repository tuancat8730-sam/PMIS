"use client";

import { useParams } from "next/navigation";

import { MatrixPage } from "../../../../components/tracking/matrix-page";
import { RiskTable } from "../../../../components/tracking/risk-table";
import { fetchRiskMatrix } from "../../../../lib/tracking";

export default function RisksPage() {
  const { projectId } = useParams<{ projectId: string }>();
  return (
    <MatrixPage
      projectId={projectId}
      title="Quản lý rủi ro"
      load={(token) => fetchRiskMatrix(projectId, token)}
      render={(data) => <RiskTable rows={data.rows} />}
    />
  );
}

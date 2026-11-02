"use client";

import { useParams } from "next/navigation";

import { ContractsView } from "../../../../components/tracking/contracts-view";
import { MatrixPage } from "../../../../components/tracking/matrix-page";
import { fetchProjectOverview } from "../../../../lib/overview";

export default function ContractsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  return (
    <MatrixPage
      projectId={projectId}
      title="Hợp đồng"
      load={(token) => fetchProjectOverview(projectId, token)}
      render={(overview) => <ContractsView contracts={overview.contracts} />}
    />
  );
}

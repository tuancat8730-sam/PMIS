"use client";

import { useParams } from "next/navigation";

import { DecisionsView } from "../../../../components/tracking/decisions-view";
import { MatrixPage } from "../../../../components/tracking/matrix-page";
import { fetchProjectOverview } from "../../../../lib/overview";

export default function DecisionsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  return (
    <MatrixPage
      projectId={projectId}
      title="Quyết định"
      load={(token) => fetchProjectOverview(projectId, token)}
      render={(overview) => <DecisionsView decisions={overview.decisions} />}
    />
  );
}

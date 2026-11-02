"use client";

import { useParams } from "next/navigation";

import { MatrixPage } from "../../../../components/tracking/matrix-page";
import { OverviewView } from "../../../../components/tracking/overview-view";
import { fetchProjectOverview } from "../../../../lib/overview";

export default function OverviewPage() {
  const { projectId } = useParams<{ projectId: string }>();
  return (
    <MatrixPage
      projectId={projectId}
      title="Tổng quan dự án"
      load={(token) => fetchProjectOverview(projectId, token)}
      render={(overview) => <OverviewView overview={overview} />}
    />
  );
}

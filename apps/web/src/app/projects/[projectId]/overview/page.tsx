"use client";

import { useParams } from "next/navigation";

import { MatrixPage } from "../../../../components/tracking/matrix-page";
import { OverviewView } from "../../../../components/tracking/overview-view";
import { fetchProjectOverview, type ProjectOverview } from "../../../../lib/overview";
import { fetchOverviewSections, type OverviewSections } from "../../../../lib/overview-sections";

interface OverviewPageData {
  overview: ProjectOverview;
  sections: OverviewSections;
}

/** Tải thông tin dự án, khoản chi và yêu cầu kỹ thuật song song. */
async function loadOverviewPage(projectId: string, token: string): Promise<OverviewPageData> {
  const [overview, sections] = await Promise.all([
    fetchProjectOverview(projectId, token),
    fetchOverviewSections(projectId, token),
  ]);
  return { overview, sections };
}

export default function OverviewPage() {
  const { projectId } = useParams<{ projectId: string }>();
  return (
    <MatrixPage
      projectId={projectId}
      title="Tổng quan dự án"
      load={(token) => loadOverviewPage(projectId, token)}
      render={({ overview, sections }) => <OverviewView overview={overview} sections={sections} />}
    />
  );
}

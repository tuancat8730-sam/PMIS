"use client";

import { useParams } from "next/navigation";

import { MatrixPage } from "../../../components/tracking/matrix-page";
import { ProjectBackLink } from "../../../components/tracking/project-back-link";
import { ProjectHomeView } from "../../../components/tracking/project-home-view";
import { fetchProjectOverview } from "../../../lib/overview";

export default function ProjectHomePage() {
  const { projectId } = useParams<{ projectId: string }>();
  return (
    <>
      <ProjectBackLink />
      <MatrixPage
        projectId={projectId}
        title="Trang chủ dự án"
        load={(token) => fetchProjectOverview(projectId, token)}
        render={(overview) => <ProjectHomeView overview={overview} />}
      />
    </>
  );
}

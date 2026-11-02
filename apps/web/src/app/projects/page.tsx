"use client";

import { MatrixPage } from "../../components/tracking/matrix-page";
import { ProjectListView } from "../../components/tracking/project-list-view";
import { fetchProjects } from "../../lib/projects";

export default function ProjectsPage() {
  return (
    <MatrixPage
      projectId="all"
      title="Danh sách dự án"
      load={(token) => fetchProjects(token)}
      render={(projects) => <ProjectListView projects={projects} />}
    />
  );
}

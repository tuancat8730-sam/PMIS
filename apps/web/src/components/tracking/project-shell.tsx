"use client";

import Link from "next/link";
import { useEffect, useState, type ReactNode } from "react";

import { fetchProjectOverview, type ProjectSummary } from "../../lib/overview";
import { readStoredToken } from "./matrix-page";
import { ProjectTabs } from "./project-tabs";

interface ProjectShellProps {
  projectId: string;
  children: ReactNode;
}

/** Khung chung của mọi màn hình theo dự án: mã và tên dự án, rồi dải tab, rồi nội dung màn hình. */
export function ProjectShell({ projectId, children }: ProjectShellProps) {
  const [project, setProject] = useState<ProjectSummary | null>(null);
  const [headerError, setHeaderError] = useState<string | null>(null);

  useEffect(() => {
    const token = readStoredToken();
    if (token === null) {
      return;
    }
    fetchProjectOverview(projectId, token)
      .then((overview) => setProject(overview.project))
      .catch((error: unknown) =>
        setHeaderError(
          error instanceof Error ? error.message : "Không tải được thông tin dự án",
        ),
      );
  }, [projectId]);

  return (
    <div className="flex flex-col">
      <header className="flex flex-col gap-1 px-6 pt-4 pb-3">
        {project !== null && (
          <Link href={`/projects/${projectId}`} className="flex flex-col gap-0.5">
            <span className="text-sm text-text-muted">{project.code}</span>
            <span className="text-base font-semibold text-primary">{project.name}</span>
          </Link>
        )}
        {headerError !== null && <p className="text-sm text-red-700">{headerError}</p>}
      </header>
      <ProjectTabs projectId={projectId} />
      {children}
    </div>
  );
}

"use client";

import { useParams } from "next/navigation";
import type { ReactNode } from "react";

import { ProjectShell } from "../../../components/tracking/project-shell";

export default function ProjectLayout({ children }: { children: ReactNode }) {
  const { projectId } = useParams<{ projectId: string }>();
  return <ProjectShell projectId={projectId}>{children}</ProjectShell>;
}

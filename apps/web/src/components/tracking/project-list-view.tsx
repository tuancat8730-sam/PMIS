import Link from "next/link";

import type { ProjectSummary } from "../../lib/overview";

export function ProjectListView({ projects }: { projects: ProjectSummary[] }) {
  if (projects.length === 0) {
    return <p className="text-neutral-500">Chưa có dự án nào.</p>;
  }
  return (
    <ul className="flex flex-col gap-3">
      {projects.map((project) => (
        <li key={project.id}>
          <Link
            href={`/projects/${project.id}`}
            className="flex flex-col gap-1 rounded-md border border-neutral-200 px-4 py-3 hover:border-neutral-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2"
          >
            <span className="text-sm text-neutral-500">{project.code}</span>
            <span className="font-semibold text-neutral-900">{project.name}</span>
          </Link>
        </li>
      ))}
    </ul>
  );
}

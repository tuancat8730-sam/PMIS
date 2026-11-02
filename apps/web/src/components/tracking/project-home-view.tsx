import Link from "next/link";

import type { ProjectOverview } from "../../lib/overview";
import { PROJECT_SECTIONS } from "./project-sections";

export function ProjectHomeView({ overview }: { overview: ProjectOverview }) {
  const { project } = overview;
  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-col gap-1">
        <p className="text-sm text-neutral-500">{project.code}</p>
        <h2 className="text-lg font-semibold text-neutral-900">{project.name}</h2>
      </header>
      <nav aria-label="Các màn hình của dự án">
        <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {PROJECT_SECTIONS.map((section) => (
            <li key={section.path}>
              <Link
                href={`/projects/${project.id}/${section.path}`}
                className="flex h-full flex-col gap-1 rounded-md border border-neutral-200 px-4 py-3 hover:border-neutral-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2"
              >
                <span className="font-semibold text-neutral-900">{section.label}</span>
                <span className="text-sm text-neutral-600">{section.description}</span>
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
}

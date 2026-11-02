import Link from "next/link";

import type { ProjectOverview } from "../../lib/overview";

interface ProjectSection {
  label: string;
  description: string;
  /** Đường dẫn con sau /projects/{id}/, có thể kèm anchor. */
  path: string;
}

export const PROJECT_SECTIONS: readonly ProjectSection[] = [
  { label: "Mốc", description: "Kế hoạch và tiến độ nghiệm thu", path: "schedule" },
  { label: "Rủi ro", description: "Rủi ro và vấn đề đang theo dõi", path: "risks" },
  { label: "Pháp lý", description: "Hồ sơ pháp lý theo giai đoạn", path: "legal" },
  { label: "File", description: "Danh mục file và bằng chứng", path: "files" },
  { label: "Quyết định", description: "Quyết định phê duyệt của dự án", path: "overview#decisions" },
  { label: "Hợp đồng", description: "Ma trận hợp đồng và giá trị", path: "overview#contracts" },
];

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

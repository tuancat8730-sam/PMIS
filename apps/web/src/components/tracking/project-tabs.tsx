"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { PROJECT_SECTIONS } from "./project-sections";

interface ProjectTabsProps {
  projectId: string;
}

/** Đường dẫn của màn hình, bỏ anchor để so khớp với pathname hiện tại. */
function screenPathname(projectId: string, path: string): string {
  const [screen] = path.split("#");
  return `/projects/${projectId}/${screen}`;
}

/** Dải tab màn hình. Trên điện thoại cuộn ngang và dính đầu trang; mỗi tab cao 44px để dễ chạm. */
export function ProjectTabs({ projectId }: ProjectTabsProps) {
  const pathname = usePathname();
  return (
    <nav
      aria-label="Điều hướng màn hình dự án"
      className="sticky top-0 z-10 overflow-x-auto border-b border-border-subtle bg-background"
    >
      <ul className="flex min-w-max gap-1 px-4">
        {PROJECT_SECTIONS.map((section) => {
          const isActive = pathname === screenPathname(projectId, section.path);
          return (
            <li key={section.path}>
              <Link
                href={`/projects/${projectId}/${section.path}`}
                aria-current={isActive ? "page" : undefined}
                className={`flex min-h-11 items-center border-b-2 px-3 text-sm font-medium ${
                  isActive
                    ? "border-accent text-primary"
                    : "border-transparent text-text-muted hover:text-primary"
                }`}
              >
                {section.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

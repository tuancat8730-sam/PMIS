import Link from "next/link";

/** Nút quay lại danh sách dự án, hiện ở đầu mọi màn hình theo dự án. Vùng chạm cao 44px. */
export function ProjectBackLink() {
  return (
    <Link
      href="/projects"
      className="inline-flex min-h-11 w-fit items-center gap-1 text-sm font-semibold text-primary underline-offset-4 hover:underline"
    >
      <span aria-hidden="true">←</span>
      Quay lại danh sách dự án
    </Link>
  );
}

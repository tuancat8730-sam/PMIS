import Link from "next/link";

/** Nút quay lại danh sách dự án, dùng ở đầu màn hình chi tiết dự án. Vùng chạm cao 44px. */
export function ProjectBackLink() {
  return (
    <Link
      href="/projects"
      className="inline-flex min-h-11 items-center gap-1 px-6 text-sm font-semibold text-primary underline-offset-4 hover:underline"
    >
      <span aria-hidden="true">←</span>
      Quay lại danh sách dự án
    </Link>
  );
}

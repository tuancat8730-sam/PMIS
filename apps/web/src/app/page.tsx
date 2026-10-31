import { fetchApiHealth, type ApiHealthStatus } from "@/lib/api";

const STATUS_COPY: Record<ApiHealthStatus, { label: string; tone: string }> = {
  ok: { label: "Đang hoạt động", tone: "text-emerald-700" },
  unreachable: { label: "Không kết nối được", tone: "text-red-700" },
};

export default async function Home() {
  const status = await fetchApiHealth();
  const { label, tone } = STATUS_COPY[status];

  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center gap-6 px-6 py-16">
      <p className="text-sm font-medium uppercase tracking-widest text-neutral-500">
        PMIS · Đầu tư công
      </p>
      <h1 className="text-4xl font-semibold leading-tight text-neutral-900">
        Quản trị và giám sát dự án
      </h1>
      <section
        aria-labelledby="api-status-heading"
        className="border-l-4 border-neutral-900 bg-neutral-50 px-5 py-4"
      >
        <h2 id="api-status-heading" className="text-sm text-neutral-500">
          Trạng thái máy chủ API
        </h2>
        <p className={`mt-1 text-lg font-semibold ${tone}`}>{label}</p>
      </section>
    </main>
  );
}

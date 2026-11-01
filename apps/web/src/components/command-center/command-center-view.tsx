import {
  filterByProject,
  formatBillionVnd,
  type CommandCenterData,
} from "../../lib/command-center";

interface CommandCenterViewProps {
  data: CommandCenterData;
  selectedCode: string | null;
  onSelectProject: (code: string | null) => void;
}

const NOT_AVAILABLE = "chưa có dữ liệu";

function KpiValue({ value }: { value: number | null }) {
  if (value === null) {
    return <span className="text-base text-neutral-500">{NOT_AVAILABLE}</span>;
  }
  return <span className="text-3xl font-semibold text-neutral-900">{value}</span>;
}

export function CommandCenterView({ data, selectedCode, onSelectProject }: CommandCenterViewProps) {
  const view = filterByProject(data, selectedCode);
  const { kpi } = data;

  return (
    <main className="mx-auto flex max-w-5xl flex-col gap-10 px-4 py-10">
      <header className="flex flex-col gap-2">
        <p className="text-sm uppercase tracking-widest text-neutral-500">Command Center</p>
        <h1 className="text-3xl font-semibold text-neutral-900">Tổng quan điều hành</h1>
        <label className="flex flex-col gap-1 text-sm text-neutral-600">
          Dự án
          <select
            className="w-64 rounded border border-neutral-300 bg-white px-3 py-2 text-neutral-900"
            value={selectedCode ?? ""}
            onChange={(event) => onSelectProject(event.target.value || null)}
          >
            <option value="">Tất cả dự án</option>
            {data.projects.map((project) => (
              <option key={project.id} value={project.code}>
                {project.code}
              </option>
            ))}
          </select>
        </label>
      </header>

      <section aria-labelledby="kpi-heading" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <h2 id="kpi-heading" className="sr-only">
          Chỉ số chính
        </h2>
        <article className="flex flex-col gap-1 border-l-4 border-neutral-900 bg-neutral-50 p-4">
          <p className="text-sm text-neutral-500">Tổng giá trị hợp đồng</p>
          <span className="text-2xl font-semibold text-neutral-900">
            {formatBillionVnd(kpi.contract_value_total)}
          </span>
          <p className="text-xs text-neutral-500">
            Gói chính {formatBillionVnd(kpi.contract_value_by_kind.MAIN ?? "0")} · Tư vấn{" "}
            {formatBillionVnd(kpi.contract_value_by_kind.CONSULTING ?? "0")}
          </p>
        </article>
        <article className="flex flex-col gap-1 border-l-4 border-neutral-900 bg-neutral-50 p-4">
          <p className="text-sm text-neutral-500">Dự án đang chạy</p>
          <KpiValue value={kpi.running_project_count} />
        </article>
        <article className="flex flex-col gap-1 border-l-4 border-neutral-900 bg-neutral-50 p-4">
          <p className="text-sm text-neutral-500">Điểm thụ hưởng</p>
          <KpiValue value={kpi.beneficiary_unit_count} />
        </article>
        <article className="flex flex-col gap-1 border-l-4 border-neutral-900 bg-neutral-50 p-4">
          <p className="text-sm text-neutral-500">Hồ sơ chờ ký</p>
          <KpiValue value={kpi.pending_signature_count} />
        </article>
      </section>

      <section aria-labelledby="red-heading" className="flex flex-col gap-3">
        <h2 id="red-heading" className="text-lg font-semibold text-red-700">
          Cảnh báo đỏ trong 48 giờ ({view.red_alerts.length})
        </h2>
        {view.red_alerts.length === 0 ? (
          <p className="text-neutral-500">Không có việc khẩn.</p>
        ) : (
          <ul className="grid gap-3 sm:grid-cols-2">
            {view.red_alerts.map((alert) => (
              <li key={`${alert.project_code}-${alert.source}-${alert.code}`}>
                <article className="border border-red-200 bg-red-50 p-4">
                  <p className="text-xs text-red-700">
                    {alert.project_code} · {alert.code}
                  </p>
                  <h3 className="font-medium text-neutral-900">{alert.title}</h3>
                  <p className="text-sm text-neutral-600">Hạn: {alert.due_date}</p>
                </article>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section aria-labelledby="countdown-heading" className="flex flex-col gap-3">
        <h2 id="countdown-heading" className="text-lg font-semibold text-neutral-900">
          Đếm ngược hợp đồng
        </h2>
        {view.contract_countdowns.length === 0 ? (
          <p className="text-neutral-500">Không có hợp đồng sắp hết hạn.</p>
        ) : (
          <ul className="flex flex-col gap-2">
            {view.contract_countdowns.map((row) => (
              <li
                key={`${row.project_code}-${row.contract_number ?? row.expiration_date}`}
                className="flex justify-between border-b border-neutral-200 py-2"
              >
                <span>
                  {row.project_code} · {row.contract_number ?? "không số"}
                </span>
                <span className="text-sm text-neutral-600">
                  {row.status === "EXPIRED"
                    ? "Đã hết hạn"
                    : `Còn ${row.days_remaining} ngày (hết hạn ${row.expiration_date})`}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section aria-labelledby="projects-heading" className="flex flex-col gap-3">
        <h2 id="projects-heading" className="text-lg font-semibold text-neutral-900">
          Sức khỏe dự án
        </h2>
        <ul className="flex flex-col gap-2">
          {view.projects.map((project) => (
            <li key={project.id} className="flex justify-between border-b border-neutral-200 py-2">
              <span>
                {project.code} · {project.short_name}
              </span>
              <span className="text-sm text-neutral-600">
                {project.health} · trễ tối đa {project.max_slippage_days} ngày
              </span>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}

import { formatVnd, type ProjectOverview } from "../../lib/overview";

function cellText(value: string | null): string {
  return value ?? "—";
}

/** Thông tin chung của dự án. Quyết định và hợp đồng có màn hình riêng. */
export function OverviewView({ overview }: { overview: ProjectOverview }) {
  const { project, decisions } = overview;
  const approval = decisions.find((decision) => decision.kind === "PROJECT_APPROVAL");
  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-base font-semibold text-neutral-800">{project.name}</h2>
      <dl className="grid grid-cols-1 gap-4 text-sm sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <dt className="text-text-muted">Tổng mức đầu tư</dt>
          <dd className="text-lg font-semibold">{formatVnd(project.total_investment)}</dd>
        </div>
        <div>
          <dt className="text-text-muted">Nguồn vốn</dt>
          <dd>{cellText(approval?.funding_source ?? null)}</dd>
        </div>
        <div>
          <dt className="text-text-muted">Thời gian thực hiện</dt>
          <dd>{cellText(approval?.execution_period ?? null)}</dd>
        </div>
        <div>
          <dt className="text-text-muted">Chủ đầu tư</dt>
          <dd>{project.investor_name}</dd>
        </div>
      </dl>
    </section>
  );
}

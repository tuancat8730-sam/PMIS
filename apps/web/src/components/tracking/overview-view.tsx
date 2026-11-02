import {
  decisionKindLabel,
  formatVnd,
  type ContractSummaryRow,
  type LegalDecisionRow,
  type ProjectOverview,
} from "../../lib/overview";
import { formatDateVi } from "../../lib/tracking";

function cellText(value: string | null): string {
  return value ?? "—";
}

function ContractsTable({ contracts }: { contracts: ContractSummaryRow[] }) {
  if (contracts.length === 0) {
    return <p className="text-neutral-500">Chưa có hợp đồng nào.</p>;
  }
  return (
    <table className="min-w-full text-left text-sm">
      <thead className="border-b text-neutral-600">
        <tr>
          <th className="px-3 py-2">Gói</th>
          <th className="px-3 py-2">Số hợp đồng</th>
          <th className="px-3 py-2">Ngày ký</th>
          <th className="px-3 py-2">Giá trị</th>
        </tr>
      </thead>
      <tbody>
        {contracts.map((contract) => (
          <tr key={contract.id} className="border-b align-top">
            <td className="px-3 py-2">{contract.package_name}</td>
            <td className="px-3 py-2">{cellText(contract.contract_number)}</td>
            <td className="px-3 py-2">{formatDateVi(contract.signed_date)}</td>
            <td className="px-3 py-2">{formatVnd(contract.contract_value)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function DecisionsTable({ decisions }: { decisions: LegalDecisionRow[] }) {
  if (decisions.length === 0) {
    return <p className="text-neutral-500">Chưa có quyết định nào.</p>;
  }
  return (
    <table className="min-w-full text-left text-sm">
      <thead className="border-b text-neutral-600">
        <tr>
          <th className="px-3 py-2">Loại</th>
          <th className="px-3 py-2">Số quyết định</th>
          <th className="px-3 py-2">Ngày</th>
          <th className="px-3 py-2">Giá trị</th>
        </tr>
      </thead>
      <tbody>
        {decisions.map((decision) => (
          <tr key={decision.id} className="border-b align-top">
            <td className="px-3 py-2">{decisionKindLabel(decision.kind)}</td>
            <td className="px-3 py-2">{decision.decision_no}</td>
            <td className="px-3 py-2">{formatDateVi(decision.decision_date)}</td>
            <td className="px-3 py-2">
              {decision.amount === null ? "—" : formatVnd(decision.amount)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export function OverviewView({ overview }: { overview: ProjectOverview }) {
  const { project, decisions, contracts } = overview;
  const approval = decisions.find((decision) => decision.kind === "PROJECT_APPROVAL");
  return (
    <div className="flex flex-col gap-8">
      <section className="flex flex-col gap-3">
        <h2 className="text-base font-semibold text-neutral-800">{project.name}</h2>
        <dl className="grid grid-cols-1 gap-4 text-sm sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <dt className="text-neutral-500">Tổng mức đầu tư</dt>
            <dd className="text-lg font-semibold">{formatVnd(project.total_investment)}</dd>
          </div>
          <div>
            <dt className="text-neutral-500">Nguồn vốn</dt>
            <dd>{cellText(approval?.funding_source ?? null)}</dd>
          </div>
          <div>
            <dt className="text-neutral-500">Thời gian thực hiện</dt>
            <dd>{cellText(approval?.execution_period ?? null)}</dd>
          </div>
          <div>
            <dt className="text-neutral-500">Chủ đầu tư</dt>
            <dd>{project.investor_name}</dd>
          </div>
        </dl>
      </section>
      <section className="flex flex-col gap-2">
        <h2 className="text-base font-semibold text-neutral-800">Quyết định pháp lý</h2>
        <div className="overflow-x-auto">
          <DecisionsTable decisions={decisions} />
        </div>
      </section>
      <section className="flex flex-col gap-2">
        <h2 className="text-base font-semibold text-neutral-800">Ma trận hợp đồng</h2>
        <div className="overflow-x-auto">
          <ContractsTable contracts={contracts} />
        </div>
      </section>
    </div>
  );
}

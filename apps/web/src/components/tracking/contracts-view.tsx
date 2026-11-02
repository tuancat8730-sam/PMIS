import { formatVnd, type ContractSummaryRow } from "../../lib/overview";
import { formatDateVi } from "../../lib/tracking";
import { EmptyState } from "./ui/empty-state";
import { ExpandableItem } from "./ui/expandable-item";
import { Field } from "./ui/field";

function ContractSummary({ contract }: { contract: ContractSummaryRow }) {
  return (
    <div className="flex flex-col gap-1">
      <p className="font-medium text-foreground">{contract.package_name}</p>
      <p className="text-sm text-text-muted">{contract.contract_number ?? "Chưa có số hợp đồng"}</p>
    </div>
  );
}

function ContractDetails({ contract }: { contract: ContractSummaryRow }) {
  return (
    <dl className="grid grid-cols-1 gap-3 rounded-md bg-surface-muted p-3 sm:grid-cols-2 lg:grid-cols-3">
      <Field
        label="Ngày ký"
        value={contract.signed_date === null ? null : formatDateVi(contract.signed_date)}
      />
      <Field
        label="Ngày hết hạn"
        value={contract.expiration_date === null ? null : formatDateVi(contract.expiration_date)}
      />
      <Field label="Giá trị hợp đồng" value={formatVnd(contract.contract_value)} />
    </dl>
  );
}

/** Hợp đồng theo gói thầu, mỗi gói một thẻ. */
export function ContractsView({ contracts }: { contracts: ContractSummaryRow[] }) {
  if (contracts.length === 0) {
    return <EmptyState message="Chưa có hợp đồng nào." />;
  }
  return (
    <ul className="flex flex-col rounded-lg border border-border-subtle px-4">
      {contracts.map((contract) => (
        <ExpandableItem
          key={contract.id}
          summary={<ContractSummary contract={contract} />}
          details={<ContractDetails contract={contract} />}
        />
      ))}
    </ul>
  );
}

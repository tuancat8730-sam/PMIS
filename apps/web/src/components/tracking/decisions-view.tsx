import {
  decisionKindLabel,
  formatVnd,
  groupDecisionsByKind,
  type LegalDecisionRow,
} from "../../lib/overview";
import { formatDateVi } from "../../lib/tracking";
import { EmptyState } from "./ui/empty-state";
import { ExpandableItem } from "./ui/expandable-item";
import { Field } from "./ui/field";

function DecisionSummary({ decision }: { decision: LegalDecisionRow }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="font-mono text-sm font-medium text-primary">{decision.decision_no}</span>
      <span className="text-sm text-text-muted">{formatDateVi(decision.decision_date)}</span>
    </div>
  );
}

function DecisionDetails({ decision }: { decision: LegalDecisionRow }) {
  return (
    <dl className="grid grid-cols-1 gap-3 rounded-md bg-surface-muted p-3 sm:grid-cols-2 lg:grid-cols-4">
      <Field label="Cơ quan ban hành" value={decision.issuing_authority} />
      <Field
        label="Số tiền"
        value={decision.amount === null ? null : formatVnd(decision.amount)}
      />
      <Field label="Nguồn vốn" value={decision.funding_source} />
      <Field label="Thời gian thực hiện" value={decision.execution_period} />
      <Field label="Ghi chú" value={decision.note} />
    </dl>
  );
}

/** Quyết định theo loại; quyết định phê duyệt dự án đứng đầu. */
export function DecisionsView({ decisions }: { decisions: LegalDecisionRow[] }) {
  const groups = groupDecisionsByKind(decisions);
  if (groups.length === 0) {
    return <EmptyState message="Chưa có quyết định nào." />;
  }
  return (
    <div className="flex flex-col gap-6">
      {groups.map((group) => (
        <section key={group.kind} className="flex flex-col gap-2">
          <h2 className="text-sm font-semibold text-primary">{decisionKindLabel(group.kind)}</h2>
          <ul className="flex flex-col rounded-lg border border-border-subtle px-4">
            {group.rows.map((decision) => (
              <ExpandableItem
                key={decision.id}
                summary={<DecisionSummary decision={decision} />}
                details={<DecisionDetails decision={decision} />}
              />
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}

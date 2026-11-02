import {
  decisionKindLabel,
  formatVnd,
  type ContractSummaryRow,
  type LegalDecisionKind,
  type LegalDecisionRow,
  type ProjectOverview,
} from "../../lib/overview";
import {
  formatDateVi,
  type BudgetItemRow,
  type OverviewSections,
  type TechnicalRequirementRow,
} from "../../lib/overview-sections";
import { EmptyState } from "./ui/empty-state";
import { Field } from "./ui/field";

const MISSING_SOURCE_TEXT = "Chưa có nguồn";
const NOT_APPLICABLE_TEXT = "—";

const APPROVAL_KINDS: readonly LegalDecisionKind[] = [
  "PROJECT_APPROVAL",
  "BCKTKT_APPROVAL",
  "KHLCNT_APPROVAL",
  "BIDDING_RESULT_APPROVAL",
];

function findDecision(
  decisions: readonly LegalDecisionRow[],
  kind: LegalDecisionKind,
): LegalDecisionRow | undefined {
  return decisions.find((decision) => decision.kind === kind);
}

/** Số QĐ kèm ngày ký, ví dụ "1595/QĐ-SGDĐT, ngày 22/05/2026". Thiếu ngày thì chỉ hiện số QĐ. */
function decisionText(decision: LegalDecisionRow | undefined): string | null {
  if (decision === undefined) {
    return null;
  }
  const date = formatDateVi(decision.decision_date);
  return date === null
    ? decision.decision_no
    : `${decision.decision_no}, ngày ${date}`;
}

function amountText(amount: string | null): string | null {
  return amount === null ? null : formatVnd(amount);
}

function SectionHeading({ id, text }: { id: string; text: string }) {
  return (
    <h2 id={id} className="text-base font-semibold text-neutral-800">
      {text}
    </h2>
  );
}

function ApprovalFields({
  decisions,
}: {
  decisions: readonly LegalDecisionRow[];
}) {
  return (
    <dl className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
      {APPROVAL_KINDS.map((kind) => (
        <Field
          key={kind}
          label={decisionKindLabel(kind)}
          value={decisionText(findDecision(decisions, kind))}
          missingText={MISSING_SOURCE_TEXT}
        />
      ))}
    </dl>
  );
}

function BudgetItemList({ items }: { items: readonly BudgetItemRow[] }) {
  if (items.length === 0) {
    return <EmptyState message="Chưa có nguồn cho chi phí theo khoản." />;
  }
  return (
    <ul className="flex flex-col divide-y divide-border-subtle text-sm">
      {items.map((item) => (
        <li
          key={item.id}
          className="flex flex-col gap-0.5 py-2 sm:flex-row sm:justify-between"
        >
          <span className="text-foreground">{item.label}</span>
          <span className="font-semibold">{formatVnd(item.amount)}</span>
          {item.note && (
            <span className="text-xs text-text-muted sm:w-full">
              {item.note}
            </span>
          )}
        </li>
      ))}
    </ul>
  );
}

function SectionOne({
  overview,
  budgetItems,
}: {
  overview: ProjectOverview;
  budgetItems: readonly BudgetItemRow[];
}) {
  const { project, decisions } = overview;
  const approval = findDecision(decisions, "PROJECT_APPROVAL");
  return (
    <section
      aria-labelledby="overview-section-1"
      className="flex flex-col gap-4"
    >
      <SectionHeading
        id="overview-section-1"
        text="I. Thông tin pháp lý và tổng mức đầu tư gói thầu"
      />
      <dl className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
        <Field
          label="Tên dự án"
          value={project.name}
          missingText={MISSING_SOURCE_TEXT}
        />
        <Field
          label="Chủ đầu tư"
          value={project.investor_name}
          missingText={MISSING_SOURCE_TEXT}
        />
        <Field
          label="Cơ quan quyết định đầu tư"
          value={project.decision_authority}
          missingText={MISSING_SOURCE_TEXT}
        />
        <Field
          label="Tổng mức đầu tư"
          value={amountText(project.total_investment)}
          missingText={MISSING_SOURCE_TEXT}
        />
        <Field
          label="Nguồn vốn"
          value={approval?.funding_source ?? null}
          missingText={MISSING_SOURCE_TEXT}
        />
        <Field
          label="Thời gian thực hiện"
          value={approval?.execution_period ?? null}
          missingText={MISSING_SOURCE_TEXT}
        />
        <Field
          label="Đại diện pháp luật"
          value={project.legal_representative}
          missingText={MISSING_SOURCE_TEXT}
        />
        <Field
          label="Hình thức QLDA"
          value={project.qlda_form}
          missingText={MISSING_SOURCE_TEXT}
        />
        <Field
          label="Hạn giải ngân"
          value={project.disbursement_deadline}
          missingText={MISSING_SOURCE_TEXT}
        />
      </dl>
      <ApprovalFields decisions={decisions} />
      <BudgetItemList items={budgetItems} />
    </section>
  );
}

function ContractList({
  contracts,
}: {
  contracts: readonly ContractSummaryRow[];
}) {
  if (contracts.length === 0) {
    return <EmptyState message="Chưa có nguồn cho ma trận hợp đồng." />;
  }
  return (
    <ul className="flex flex-col gap-3">
      {contracts.map((contract) => (
        <li
          key={contract.id}
          className="grid grid-cols-1 gap-3 rounded-lg border border-border-subtle p-3 text-sm sm:grid-cols-2 lg:grid-cols-4"
        >
          <Field
            label="Vai trò"
            value={contract.role_label ?? contract.package_name}
            missingText={MISSING_SOURCE_TEXT}
          />
          <Field
            label="Đơn vị thực hiện"
            value={contract.contractor_name}
            missingText={MISSING_SOURCE_TEXT}
          />
          <Field
            label="Số hợp đồng"
            value={contract.contract_number}
            missingText={MISSING_SOURCE_TEXT}
          />
          <Field
            label="Ngày ký"
            value={formatDateVi(contract.signed_date)}
            missingText={MISSING_SOURCE_TEXT}
          />
          <Field
            label="Thời hạn"
            value={formatDateVi(contract.expiration_date)}
            missingText={MISSING_SOURCE_TEXT}
          />
          <Field
            label="Giá trị"
            value={amountText(contract.contract_value)}
            missingText={MISSING_SOURCE_TEXT}
          />
          <Field
            label="Đầu mối"
            value={contract.contact_person}
            missingText={MISSING_SOURCE_TEXT}
          />
          <Field
            label="Hiện trạng và đánh giá"
            value={contract.status_note}
            missingText={MISSING_SOURCE_TEXT}
          />
        </li>
      ))}
    </ul>
  );
}

/** Chủ đầu tư không phải hợp đồng nên hiển thị thành một dòng riêng, các ô không áp dụng ghi "—". */
function OwnerCard({ overview }: { overview: ProjectOverview }) {
  const { project, decisions } = overview;
  const approval = findDecision(decisions, "PROJECT_APPROVAL");
  return (
    <div className="grid grid-cols-1 gap-3 rounded-lg border border-border-subtle bg-neutral-50 p-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
      <Field
        label="Vai trò"
        value="Chủ đầu tư (CĐT)"
        missingText={MISSING_SOURCE_TEXT}
      />
      <Field
        label="Đơn vị thực hiện"
        value={project.investor_name}
        missingText={MISSING_SOURCE_TEXT}
      />
      <Field
        label="Số hợp đồng"
        value={NOT_APPLICABLE_TEXT}
        missingText={MISSING_SOURCE_TEXT}
      />
      <Field
        label="Ngày ký"
        value={NOT_APPLICABLE_TEXT}
        missingText={MISSING_SOURCE_TEXT}
      />
      <Field
        label="Thời hạn"
        value={approval?.execution_period ?? null}
        missingText={MISSING_SOURCE_TEXT}
      />
      <Field
        label="Giá trị"
        value={amountText(project.total_investment)}
        missingText={MISSING_SOURCE_TEXT}
      />
      <Field label="Đầu mối" value={null} missingText={MISSING_SOURCE_TEXT} />
      <Field
        label="Hiện trạng và đánh giá"
        value={null}
        missingText={MISSING_SOURCE_TEXT}
      />
    </div>
  );
}

function SectionTwo({ overview }: { overview: ProjectOverview }) {
  return (
    <section
      aria-labelledby="overview-section-2"
      className="flex flex-col gap-4"
    >
      <SectionHeading
        id="overview-section-2"
        text="II. Ma trận hợp đồng và các đơn vị thực hiện"
      />
      <OwnerCard overview={overview} />
      <ContractList contracts={overview.contracts} />
    </section>
  );
}

function RequirementList({
  requirements,
}: {
  requirements: readonly TechnicalRequirementRow[];
}) {
  if (requirements.length === 0) {
    return (
      <EmptyState message="Chưa có nguồn cho mục III. Cần bản đọc rõ của báo cáo gốc." />
    );
  }
  return (
    <ul className="flex flex-col gap-3">
      {requirements.map((requirement) => (
        <li
          key={requirement.id}
          className="flex flex-col gap-3 rounded-lg border border-border-subtle p-3 text-sm"
        >
          <p className="font-semibold text-foreground">{requirement.item}</p>
          <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Field
              label="Quy chuẩn"
              value={requirement.standard}
              missingText={MISSING_SOURCE_TEXT}
            />
            <Field
              label="Căn cứ pháp lý"
              value={requirement.legal_basis}
              missingText={MISSING_SOURCE_TEXT}
            />
            <Field
              label="Mô tả giải pháp"
              value={requirement.solution}
              missingText={MISSING_SOURCE_TEXT}
            />
            <Field
              label="Trách nhiệm thực hiện"
              value={requirement.responsibility}
              missingText={MISSING_SOURCE_TEXT}
            />
            <Field
              label="Tiêu chuẩn nghiệm thu"
              value={requirement.acceptance_criteria}
              missingText={MISSING_SOURCE_TEXT}
            />
            <Field
              label="Rủi ro liên quan"
              value={requirement.related_risk}
              missingText={MISSING_SOURCE_TEXT}
            />
            <Field
              label="Trạng thái giám sát"
              value={requirement.monitoring_status}
              missingText={MISSING_SOURCE_TEXT}
            />
          </dl>
        </li>
      ))}
    </ul>
  );
}

function SectionThree({
  requirements,
}: {
  requirements: readonly TechnicalRequirementRow[];
}) {
  return (
    <section
      aria-labelledby="overview-section-3"
      className="flex flex-col gap-4"
    >
      <SectionHeading
        id="overview-section-3"
        text="III. Quy mô kỹ thuật và chỉ tiêu nghiệm thu ràng buộc"
      />
      <RequirementList requirements={requirements} />
    </section>
  );
}

/** Tổng quan dự án theo ba mục của báo cáo mẫu. Dữ liệu thiếu hiện "Chưa có nguồn", không suy đoán. */
export function OverviewView({
  overview,
  sections,
}: {
  overview: ProjectOverview;
  sections: OverviewSections;
}) {
  return (
    <div className="flex flex-col gap-8">
      <SectionOne overview={overview} budgetItems={sections.budgetItems} />
      <SectionTwo overview={overview} />
      <SectionThree requirements={sections.requirements} />
    </div>
  );
}

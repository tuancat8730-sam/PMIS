import {
  groupLegalDocumentsByPhase,
  legalPhaseLabel,
  legalStatusLabel,
  type LegalDocumentRow,
} from "../../lib/legal";
import { formatDateVi } from "../../lib/tracking";

export function LegalTable({ rows }: { rows: LegalDocumentRow[] }) {
  const groups = groupLegalDocumentsByPhase(rows);
  if (groups.length === 0) {
    return <p className="text-neutral-500">Chưa có hồ sơ pháp lý nào.</p>;
  }
  return (
    <div className="flex flex-col gap-6">
      {groups.map((group) => (
        <section key={group.phase} className="flex flex-col gap-2">
          <h2 className="text-base font-semibold text-neutral-800">
            {legalPhaseLabel(group.phase)}
          </h2>
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b text-neutral-600">
                <tr>
                  <th className="px-3 py-2">STT</th>
                  <th className="px-3 py-2">Văn bản / hồ sơ</th>
                  <th className="px-3 py-2">Số hiệu</th>
                  <th className="px-3 py-2">Đơn vị ký</th>
                  <th className="px-3 py-2">Ngày ban hành</th>
                  <th className="px-3 py-2">Tình trạng</th>
                </tr>
              </thead>
              <tbody>
                {group.rows.map((row) => (
                  <tr key={row.id} className="border-b align-top">
                    <td className="px-3 py-2">{row.stt ?? "—"}</td>
                    <td className="px-3 py-2">{row.doc_name}</td>
                    <td className="px-3 py-2">{row.doc_code_symbol ?? "—"}</td>
                    <td className="px-3 py-2">{row.issuing_authority ?? "—"}</td>
                    <td className="px-3 py-2">{formatDateVi(row.issue_date)}</td>
                    <td className="px-3 py-2">{legalStatusLabel(row.maturity_status)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ))}
    </div>
  );
}

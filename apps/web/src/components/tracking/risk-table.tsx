import { formatDateVi, riskLevelLabel, type RiskRow } from "../../lib/tracking";

export function RiskTable({ rows }: { rows: RiskRow[] }) {
  if (rows.length === 0) {
    return <p className="text-neutral-500">Chưa có rủi ro nào.</p>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-left text-sm">
        <thead className="border-b text-neutral-600">
          <tr>
            <th className="px-3 py-2">Mã</th>
            <th className="px-3 py-2">Rủi ro</th>
            <th className="px-3 py-2">Tác động</th>
            <th className="px-3 py-2">Khả năng</th>
            <th className="px-3 py-2">Điểm</th>
            <th className="px-3 py-2">Người phụ trách</th>
            <th className="px-3 py-2">Hạn xử lý</th>
            <th className="px-3 py-2">Đơn vị phối hợp</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} className="border-b align-top">
              <td className="px-3 py-2 font-medium">{row.code}</td>
              <td className="px-3 py-2">{row.title}</td>
              <td className="px-3 py-2">{riskLevelLabel(row.impact)}</td>
              <td className="px-3 py-2">{riskLevelLabel(row.likelihood)}</td>
              <td className="px-3 py-2">{row.score ?? "—"}</td>
              <td className="px-3 py-2">{row.owner ?? "—"}</td>
              <td className="px-3 py-2">{formatDateVi(row.due_date)}</td>
              <td className="px-3 py-2">{row.coordinating_units ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

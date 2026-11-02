import { formatDateVi, milestoneStatusLabel, type ScheduleRow } from "../../lib/tracking";

export function ScheduleTable({ rows }: { rows: ScheduleRow[] }) {
  if (rows.length === 0) {
    return <p className="text-neutral-500">Chưa có mốc tiến độ.</p>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-left text-sm">
        <thead className="border-b text-neutral-600">
          <tr>
            <th className="px-3 py-2">Mã</th>
            <th className="px-3 py-2">Mốc</th>
            <th className="px-3 py-2">Hạn gốc</th>
            <th className="px-3 py-2">Trạng thái</th>
            <th className="px-3 py-2">Tiến độ</th>
            <th className="px-3 py-2">Sản phẩm bàn giao</th>
            <th className="px-3 py-2">Điều kiện nghiệm thu</th>
            <th className="px-3 py-2">Mốc TVGS</th>
            <th className="px-3 py-2">Ghi chú PM</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} className="border-b align-top">
              <td className="px-3 py-2 font-medium">{row.code}</td>
              <td className="px-3 py-2">{row.name}</td>
              <td className="px-3 py-2">{formatDateVi(row.baseline_end)}</td>
              <td className="px-3 py-2">{milestoneStatusLabel(row.display_status)}</td>
              <td className="px-3 py-2">{row.progress_percent}%</td>
              <td className="px-3 py-2">{row.deliverables ?? "—"}</td>
              <td className="px-3 py-2">{row.acceptance_conditions ?? "—"}</td>
              <td className="px-3 py-2">{row.tvgs_checkpoint ?? "—"}</td>
              <td className="px-3 py-2">{row.pm_comment ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

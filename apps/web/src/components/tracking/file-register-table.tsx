import { sortFileRegister, type FileRegisterRow } from "../../lib/file-register";

function cellText(value: string | null): string {
  return value ?? "—";
}

export function FileRegisterTable({ rows }: { rows: FileRegisterRow[] }) {
  const entries = sortFileRegister(rows);
  if (entries.length === 0) {
    return <p className="text-neutral-500">Chưa có file nào trong danh mục.</p>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-left text-sm">
        <thead className="border-b text-neutral-600">
          <tr>
            <th className="px-3 py-2">STT</th>
            <th className="px-3 py-2">Thư mục</th>
            <th className="px-3 py-2">Tên file</th>
            <th className="px-3 py-2">Định dạng</th>
            <th className="px-3 py-2">Vị trí lưu</th>
            <th className="px-3 py-2">Mục đích</th>
            <th className="px-3 py-2">Tình trạng pháp lý</th>
            <th className="px-3 py-2">Bảo mật / sở hữu</th>
            <th className="px-3 py-2">Hành động tiếp theo</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => (
            <tr key={entry.id} className="border-b align-top">
              <td className="px-3 py-2">{entry.stt}</td>
              <td className="px-3 py-2">{cellText(entry.folder_path)}</td>
              <td className="px-3 py-2">{entry.file_name}</td>
              <td className="px-3 py-2">{cellText(entry.file_format)}</td>
              <td className="px-3 py-2">{cellText(entry.storage_location)}</td>
              <td className="px-3 py-2">{cellText(entry.purpose)}</td>
              <td className="px-3 py-2">{cellText(entry.legal_status)}</td>
              <td className="px-3 py-2">{cellText(entry.security_ownership)}</td>
              <td className="px-3 py-2">{cellText(entry.next_action)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

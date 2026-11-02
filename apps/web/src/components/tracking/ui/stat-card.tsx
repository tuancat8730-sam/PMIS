interface StatCardProps {
  label: string;
  value: string;
  hint?: string;
}

/** Ô chỉ số tóm tắt đầu màn hình. Giá trị đã được định dạng sẵn bởi người gọi. */
export function StatCard({ label, value, hint }: StatCardProps) {
  return (
    <div className="flex flex-col gap-1 rounded-lg border border-border-subtle bg-background p-4">
      <p className="text-sm text-text-muted">{label}</p>
      <p className="text-2xl font-semibold text-primary">{value}</p>
      {hint && <p className="text-xs text-text-muted">{hint}</p>}
    </div>
  );
}

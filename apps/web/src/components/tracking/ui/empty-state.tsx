interface EmptyStateProps {
  message: string;
}

/** Thông báo khi danh sách trống. Nội dung là câu tiếng Việt đầy đủ, không suy đoán thay dữ liệu. */
export function EmptyState({ message }: EmptyStateProps) {
  return (
    <p className="rounded-lg border border-dashed border-border-subtle px-4 py-6 text-center text-text-muted">
      {message}
    </p>
  );
}

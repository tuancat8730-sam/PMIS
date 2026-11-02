const MISSING_VALUE_TEXT = "Chưa có thông tin";

interface FieldProps {
  label: string;
  value: string | null;
  missingText?: string;
}

/** Cặp nhãn và giá trị. Khi thiếu dữ liệu thì hiện câu báo thiếu, không suy đoán thay. */
export function Field({ label, value, missingText = MISSING_VALUE_TEXT }: FieldProps) {
  return (
    <div className="flex flex-col gap-0.5">
      <dt className="text-xs text-text-muted">{label}</dt>
      <dd className="text-sm text-foreground">{value ?? missingText}</dd>
    </div>
  );
}

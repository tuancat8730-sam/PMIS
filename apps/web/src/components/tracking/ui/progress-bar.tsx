const PERCENT_MIN = 0;
const PERCENT_MAX = 100;

interface ProgressBarProps {
  label: string;
  percent: number;
}

/** Thanh tiến độ theo phần trăm. Giá trị ngoài 0–100 được kẹp lại. */
export function ProgressBar({ label, percent }: ProgressBarProps) {
  const clamped = Math.min(Math.max(percent, PERCENT_MIN), PERCENT_MAX);
  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={PERCENT_MIN}
      aria-valuemax={PERCENT_MAX}
      aria-valuenow={clamped}
      className="h-2 w-full overflow-hidden rounded-full bg-tone-neutral-bg"
    >
      <div className="h-full rounded-full bg-accent" style={{ width: `${clamped}%` }} />
    </div>
  );
}

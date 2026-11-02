import type { Tone } from "../../../lib/tone";
import { TONE_CLASSES } from "./tone-classes";

interface StatusChipProps {
  tone: Tone;
  label: string;
}

/** Nhãn trạng thái có màu theo mức nghiêm trọng. Luôn có chữ, không chỉ dựa vào màu. */
export function StatusChip({ tone, label }: StatusChipProps) {
  return (
    <span
      className={`inline-flex items-center whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-medium ${TONE_CLASSES[tone]}`}
    >
      {label}
    </span>
  );
}

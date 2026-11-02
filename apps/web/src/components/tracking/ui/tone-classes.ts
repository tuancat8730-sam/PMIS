import type { Tone } from "../../../lib/tone";

/** Lớp Tailwind cho nền và chữ của từng mức. Tên lớp viết đủ để Tailwind quét được. */
export const TONE_CLASSES: Record<Tone, string> = {
  neutral: "bg-tone-neutral-bg text-tone-neutral-fg",
  low: "bg-tone-low-bg text-tone-low-fg",
  medium: "bg-tone-medium-bg text-tone-medium-fg",
  high: "bg-tone-high-bg text-tone-high-fg",
  critical: "bg-tone-critical-bg text-tone-critical-fg",
};

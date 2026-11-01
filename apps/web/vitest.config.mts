import { defineConfig } from "vitest/config";

// Next.js biên dịch JSX theo kiểu tự động (không cần import React). Vitest cần cùng cấu hình này.
export default defineConfig({
  esbuild: {
    jsx: "automatic",
  },
});

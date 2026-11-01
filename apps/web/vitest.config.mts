import { configDefaults, defineConfig } from "vitest/config";

// Next.js biên dịch JSX theo kiểu tự động (không cần import React). Vitest cần cùng cấu hình này.
// Loại e2e/: spec Playwright không chạy dưới Vitest.
export default defineConfig({
  esbuild: {
    jsx: "automatic",
  },
  test: {
    exclude: [...configDefaults.exclude, "e2e/**"],
  },
});

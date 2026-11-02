import { expect, test, type Page, type Route } from "@playwright/test";

const TOKEN_KEY = "pmis.field.token";
const TEST_TOKEN = "e2e-token-drive";
const PROJECT_ID = "p1";
const PDF_ID = "drive-pdf-1";
const DOCX_ID = "drive-docx-1";

const FILES = [
  {
    id: "row-pdf",
    drive_file_id: PDF_ID,
    drive_path: "5.Nghiem thu/bien_ban_nghiem_thu.pdf",
    file_name: "bien_ban_nghiem_thu.pdf",
    mime_type: "application/pdf",
    file_size: 204800,
    web_view_link: "https://drive.example/pdf",
    modified_time: "2026-10-01T00:00:00Z",
    last_synced_at: "2026-11-02T08:00:00Z",
  },
  {
    id: "row-docx",
    drive_file_id: DOCX_ID,
    drive_path: "bao_cao_tuan.docx",
    file_name: "bao_cao_tuan.docx",
    mime_type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    file_size: 51200,
    web_view_link: "https://drive.example/docx",
    modified_time: "2026-10-05T00:00:00Z",
    last_synced_at: "2026-11-02T08:00:00Z",
  },
];

const SYNC_COUNTS = { scanned: 2, created: 1, updated: 0, removed: 0 };

async function mockDriveApi(page: Page): Promise<void> {
  await page.addInitScript(
    ([key, token]) => window.localStorage.setItem(key, token),
    [TOKEN_KEY, TEST_TOKEN],
  );
  await page.route(`**/api/v1/projects/${PROJECT_ID}/drive/**`, (route: Route) => {
    const { pathname } = new URL(route.request().url());
    if (pathname.endsWith("/drive/sync")) {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(SYNC_COUNTS),
      });
    }
    if (pathname.endsWith(`/files/${PDF_ID}/content`)) {
      return route.fulfill({
        status: 200,
        contentType: "application/pdf",
        body: "%PDF-1.4\n%%EOF",
      });
    }
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(FILES),
    });
  });
}

async function openViewerFor(page: Page, fileName: string): Promise<void> {
  await page
    .getByRole("listitem")
    .filter({ hasText: fileName })
    .getByRole("button", { name: "Xem" })
    .click();
}

test.describe("Tệp Drive: danh sách và xem trực tiếp", () => {
  test("hiển thị file theo thư mục và tên file", async ({ page }) => {
    // Arrange
    await mockDriveApi(page);

    // Act
    await page.goto(`/projects/${PROJECT_ID}/drive`);

    // Assert
    await expect(page.getByText("bien_ban_nghiem_thu.pdf")).toBeVisible();
    await expect(page.getByText("bao_cao_tuan.docx")).toBeVisible();
    await expect(page.getByRole("button", { name: "Quét ngay" })).toBeVisible();
  });

  test("mở PDF trong hộp thoại xem trực tiếp", async ({ page }) => {
    // Arrange
    await mockDriveApi(page);
    await page.goto(`/projects/${PROJECT_ID}/drive`);

    // Act
    await openViewerFor(page, "bien_ban_nghiem_thu.pdf");

    // Assert
    const dialog = page.getByRole("dialog");
    await expect(dialog.getByText("bien_ban_nghiem_thu.pdf")).toBeVisible();
    await expect(dialog.locator("iframe")).toBeAttached();
  });

  test("file Word hiện thông báo và nút tải về", async ({ page }) => {
    // Arrange
    await mockDriveApi(page);
    await page.goto(`/projects/${PROJECT_ID}/drive`);

    // Act
    await openViewerFor(page, "bao_cao_tuan.docx");

    // Assert
    const dialog = page.getByRole("dialog");
    await expect(dialog.getByText("Loại file này không xem trực tiếp được")).toBeVisible();
    await expect(dialog.getByRole("button", { name: "Tải về" })).toBeVisible();
  });

  test("quét ngay hiện kết quả đồng bộ", async ({ page }) => {
    // Arrange
    await mockDriveApi(page);
    await page.goto(`/projects/${PROJECT_ID}/drive`);

    // Act
    await page.getByRole("button", { name: "Quét ngay" }).click();

    // Assert
    await expect(page.getByRole("status")).toContainText("Đã quét 2 file");
  });

  test("không cuộn ngang trên màn hình 375px", async ({ page }) => {
    // Arrange
    await page.setViewportSize({ width: 375, height: 800 });
    await mockDriveApi(page);

    // Act
    await page.goto(`/projects/${PROJECT_ID}/drive`);
    await expect(page.getByText("bien_ban_nghiem_thu.pdf")).toBeVisible();
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );

    // Assert
    expect(overflow).toBeLessThanOrEqual(0);
  });
});

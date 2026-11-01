import { expect, test, type Page, type Route } from "@playwright/test";

import { COMMAND_CENTER_FIXTURE } from "./fixtures/command-center-data";

const TOKEN_KEY = "pmis.field.token";
const TEST_TOKEN = "e2e-token-123";
const API_PATTERN = "**/api/v1/command-center";

async function seedToken(page: Page): Promise<void> {
  await page.addInitScript(
    ([key, token]) => window.localStorage.setItem(key, token),
    [TOKEN_KEY, TEST_TOKEN],
  );
}

async function mockApi(page: Page, handler: (route: Route) => Promise<void> | void): Promise<void> {
  await page.route(API_PATTERN, handler);
}

function jsonOk(route: Route): Promise<void> {
  return route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify(COMMAND_CENTER_FIXTURE),
  });
}

test.describe("Command Center: phiên đăng nhập", () => {
  test("yêu cầu đăng nhập khi chưa có token", async ({ page }) => {
    // Arrange: không seed token

    // Act
    await page.goto("/command-center");

    // Assert
    await expect(page.getByText("Chưa có phiên đăng nhập")).toBeVisible();
  });
});

test.describe("Command Center: hiển thị dữ liệu", () => {
  test("gửi Bearer token và hiển thị KPI, thẻ đỏ, đếm ngược", async ({ page }) => {
    // Arrange
    await seedToken(page);
    let authorization: string | undefined;
    await mockApi(page, async (route) => {
      authorization = route.request().headers()["authorization"];
      await jsonOk(route);
    });

    // Act
    await page.goto("/command-center");

    // Assert
    await expect(page.getByRole("heading", { name: "Tổng quan điều hành" })).toBeVisible();
    await expect(page.getByText("Mốc khẩn A")).toBeVisible();
    await expect(page.getByText("Rủi ro khẩn B")).toBeVisible();
    await expect(page.getByText("Còn 19 ngày")).toBeVisible();
    await expect(page.getByText("chưa có dữ liệu")).toBeVisible();
    expect(authorization).toBe(`Bearer ${TEST_TOKEN}`);
  });

  test("hiển thị tổng hợp đồng theo tỷ đồng", async ({ page }) => {
    // Arrange
    await seedToken(page);
    await mockApi(page, jsonOk);

    // Act
    await page.goto("/command-center");

    // Assert: 112.190.000.000 đồng = 112,19 tỷ
    await expect(page.getByText("112,19 tỷ")).toBeVisible();
  });
});

test.describe("Command Center: lọc theo dự án", () => {
  test("chọn một dự án chỉ giữ cảnh báo của dự án đó", async ({ page }) => {
    // Arrange
    await seedToken(page);
    await mockApi(page, jsonOk);
    await page.goto("/command-center");
    await expect(page.getByText("Mốc khẩn A")).toBeVisible();

    // Act
    await page.getByRole("combobox").selectOption("CC-B");

    // Assert
    await expect(page.getByText("Mốc khẩn A")).toHaveCount(0);
    await expect(page.getByText("Rủi ro khẩn B")).toBeVisible();
  });
});

test.describe("Command Center: lỗi từ API", () => {
  test("báo lỗi khi API trả 401", async ({ page }) => {
    // Arrange
    await seedToken(page);
    await mockApi(page, (route) =>
      route.fulfill({ status: 401, contentType: "application/json", body: "{}" }),
    );

    // Act
    await page.goto("/command-center");

    // Assert
    await expect(page.getByText("Command Center trả về mã 401")).toBeVisible();
  });

  test("báo lỗi khi dữ liệu trả về sai hình dạng", async ({ page }) => {
    // Arrange
    await seedToken(page);
    await mockApi(page, (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: '{"x":1}' }),
    );

    // Act
    await page.goto("/command-center");

    // Assert
    await expect(page.getByText("Dữ liệu Command Center không hợp lệ")).toBeVisible();
  });
});

test("chụp ảnh màn hình trạng thái đầy đủ để kiểm tra bằng mắt", async ({ page }, testInfo) => {
  // Arrange
  await seedToken(page);
  await mockApi(page, jsonOk);

  // Act
  await page.goto("/command-center");
  await expect(page.getByText("Mốc khẩn A")).toBeVisible();
  await page.screenshot({
    path: testInfo.outputPath(`command-center-${testInfo.project.name}.png`),
    fullPage: true,
  });
});

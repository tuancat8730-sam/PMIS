import { expect, test, type Page, type Route } from "@playwright/test";

const TOKEN_KEY = "pmis.field.token";
const TEST_TOKEN = "e2e-token-tracking";
const PROJECT_ID = "p1";
const OVERFLOW_CHECK_WIDTHS = [375, 1280];
const TRACKING_SCREENS = [
  "overview",
  "schedule",
  "risks",
  "legal",
  "files",
  "decisions",
  "contracts",
];

const PROJECT = {
  id: PROJECT_ID,
  code: "SGD-HCM-CSVC-2026",
  name: "Xây dựng hệ thống quản lý dữ liệu về cơ sở vật chất",
  investor_name: "Sở GD&ĐT TP.HCM",
  decision_authority: "UBND TP.HCM",
  total_investment: "5999498939.00",
  start_date: null,
  end_date: null,
};

const DECISION = {
  id: "d1",
  kind: "PROJECT_APPROVAL",
  decision_no: "1595/QĐ-SGDĐT",
  decision_date: "2026-05-22",
  issuing_authority: "Sở GD&ĐT TP.HCM",
  amount: "5999498939.00",
  funding_source: "Ngân sách Nhà nước",
  execution_period: "2026 - 2027",
  note: null,
};

const CONTRACT = {
  id: "c1",
  project_id: PROJECT_ID,
  package_name: "Gói triển khai",
  package_kind: "IMPLEMENTATION",
  contract_number: "29/HĐKT-DVN",
  signed_date: "2026-09-21",
  expiration_date: null,
  contract_value: "4848186000.00",
};

const FILE_ENTRY = {
  id: "f1",
  project_id: PROJECT_ID,
  stt: 4,
  folder_path: "Tài liệu lưu trữ / 2.Thủ tục",
  file_name: "1595_QD phe duyet du an...signed.pdf",
  file_format: "PDF Signed",
  storage_location: "Google Drive",
  purpose: "Quyết định phê duyệt dự án",
  legal_status: "Bản scan ký chính thức",
  security_ownership: "Pháp lý CĐT",
  next_action: "Căn cứ pháp lý nghiệm thu gốc",
  drive_file_id: null,
};

const LEGAL_DOCUMENT = {
  id: "d2",
  project_id: PROJECT_ID,
  stt: 1,
  phase_group: "PREPARATION",
  doc_code_symbol: "1595/QĐ-SGDĐT",
  doc_name: "QĐ phê duyệt chủ trương đầu tư",
  issuing_authority: "Sở GD&ĐT TP.HCM",
  issue_date: "2026-05-22",
  is_mandatory: true,
  maturity_status: "SIGNED_SCAN_PDF",
  pm_action_required: null,
  assigned_to: null,
  due_date: null,
  notes: null,
};

const SCHEDULE_MATRIX = {
  total: 1,
  rows: [
    {
      id: "m1",
      project_id: PROJECT_ID,
      code: "M1",
      name: "Điều chỉnh mốc khảo sát",
      baseline_start: null,
      baseline_end: "2026-10-30",
      adjusted_start: null,
      adjusted_end: null,
      actual_end: null,
      is_hard_deadline: false,
      progress_percent: "40",
      status: "IN_PROGRESS",
      display_status: "IN_PROGRESS",
      slippage_days: 0,
      responsible_party: null,
      evidence_summary: null,
      deliverables: null,
      acceptance_conditions: null,
      tvgs_checkpoint: null,
      pm_comment: null,
    },
  ],
};

const RISK_MATRIX = {
  total: 1,
  rows: [
    {
      id: "r1",
      code: "R02",
      record_type: "RISK",
      title: "Tiến độ gắt",
      status: "OPEN",
      owner: null,
      due_date: null,
      impact: "HIGH",
      likelihood: "VERY_HIGH",
      score: 12,
      coordinating_units: null,
    },
  ],
};

function bodyForPath(path: string): unknown {
  if (path.endsWith("/schedule-matrix")) return SCHEDULE_MATRIX;
  if (path.endsWith("/risk-matrix")) return RISK_MATRIX;
  if (path.endsWith("/legal-documents")) return [LEGAL_DOCUMENT];
  if (path.endsWith("/file-register")) return [FILE_ENTRY];
  if (path.endsWith("/legal-decisions")) return [DECISION];
  if (path.endsWith("/contracts")) return [CONTRACT];
  return PROJECT;
}

async function openTrackingPage(page: Page, screen: string): Promise<void> {
  await page.addInitScript(
    ([key, token]) => window.localStorage.setItem(key, token),
    [TOKEN_KEY, TEST_TOKEN],
  );
  await page.route(`**/api/v1/projects/${PROJECT_ID}**`, (route: Route) => {
    const { pathname } = new URL(route.request().url());
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(bodyForPath(pathname)),
    });
  });
  await page.goto(`/projects/${PROJECT_ID}/${screen}`);
}

test.describe("Tracking: các màn hình theo dự án", () => {
  test("tiến độ hiển thị tên mốc", async ({ page }) => {
    // Arrange
    // Act
    await openTrackingPage(page, "schedule");

    // Assert
    await expect(page.getByText("Điều chỉnh mốc khảo sát")).toBeVisible();
  });

  test("rủi ro hiển thị tiêu đề rủi ro", async ({ page }) => {
    // Arrange
    // Act
    await openTrackingPage(page, "risks");

    // Assert
    await expect(page.getByText("Tiến độ gắt")).toBeVisible();
  });

  test("pháp lý hiển thị tên hồ sơ", async ({ page }) => {
    // Arrange
    // Act
    await openTrackingPage(page, "legal");

    // Assert
    await expect(page.getByText("QĐ phê duyệt chủ trương đầu tư")).toBeVisible();
  });

  test("file hiển thị tên file trong danh mục", async ({ page }) => {
    // Arrange
    // Act
    await openTrackingPage(page, "files");

    // Assert
    await expect(page.getByText("1595_QD phe duyet du an...signed.pdf")).toBeVisible();
  });

  test("tổng quan hiển thị tổng mức đầu tư", async ({ page }) => {
    // Arrange
    // Act
    await openTrackingPage(page, "overview");

    // Assert
    await expect(page.getByText("5.999.498.939 đ").first()).toBeVisible();
  });

  test("quyết định hiển thị số quyết định phê duyệt", async ({ page }) => {
    // Arrange
    // Act
    await openTrackingPage(page, "decisions");

    // Assert
    await expect(page.getByText("1595/QĐ-SGDĐT")).toBeVisible();
  });

  test("hợp đồng hiển thị số hợp đồng", async ({ page }) => {
    // Arrange
    // Act
    await openTrackingPage(page, "contracts");

    // Assert
    await expect(page.getByText("29/HĐKT-DVN")).toBeVisible();
  });

  for (const width of OVERFLOW_CHECK_WIDTHS) {
    test(`không tràn ngang ở ${width}px trên mọi màn hình`, async ({ page }) => {
      // Arrange
      await page.setViewportSize({ width, height: 800 });

      // Act and Assert
      for (const screen of TRACKING_SCREENS) {
        await openTrackingPage(page, screen);
        await expect(page.locator("main h1")).toBeVisible();
        const overflowPx = await page.evaluate(
          () => document.documentElement.scrollWidth - window.innerWidth,
        );
        expect(overflowPx, `màn ${screen}`).toBeLessThanOrEqual(0);
      }
    });
  }
});

import { expect, test, type Page, type Route } from "@playwright/test";

const TOKEN_KEY = "pmis.field.token";
const PROJECT_ID = "p1";
const MILESTONE_ID = "m1";
const USER_ID = "user-1";
const TASK_NAME = "Khảo sát hiện trạng";

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

interface TaskState {
  tasks: Array<Record<string, unknown>>;
  postedTasks: Array<Record<string, unknown>>;
}

/** JWT giả chỉ có payload; giao diện chỉ đọc sub và role, server thật không được gọi. */
function tokenFor(globalRole: string): string {
  const payload = Buffer.from(JSON.stringify({ sub: USER_ID, role: globalRole })).toString(
    "base64url",
  );
  return `header.${payload}.signature`;
}

function scheduleBody(tasks: Array<Record<string, unknown>>): unknown {
  return {
    total: 1,
    rows: [
      {
        id: MILESTONE_ID,
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
        tasks,
        notes: [],
      },
    ],
  };
}

function fulfillJson(route: Route, body: unknown, status = 200): Promise<void> {
  return route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

async function openSchedule(page: Page, globalRole: string, memberRole: string, state: TaskState) {
  await page.addInitScript(
    ([key, token]) => window.localStorage.setItem(key, token),
    [TOKEN_KEY, tokenFor(globalRole)],
  );
  await page.route(`**/api/v1/projects/${PROJECT_ID}**`, (route) => {
    const request = route.request();
    const { pathname } = new URL(request.url());
    if (pathname === `/api/v1/projects/${PROJECT_ID}`) {
      return fulfillJson(route, PROJECT);
    }
    if (pathname.endsWith("/members")) {
      return fulfillJson(route, [{ user_id: USER_ID, role: memberRole, project_id: PROJECT_ID }]);
    }
    if (pathname.endsWith("/schedule-matrix")) {
      return fulfillJson(route, scheduleBody(state.tasks));
    }
    if (pathname.endsWith("/tasks") && request.method() === "POST") {
      const body = request.postDataJSON() as Record<string, unknown>;
      state.postedTasks.push(body);
      const created = { id: `t${state.tasks.length + 1}`, milestone_id: MILESTONE_ID, is_overdue: false, ...body };
      state.tasks.push(created);
      return fulfillJson(route, created, 201);
    }
    return fulfillJson(route, { detail: "Không khớp mock" }, 404);
  });
  await page.goto(`/projects/${PROJECT_ID}/schedule`);
}

async function expandMilestone(page: Page): Promise<void> {
  await expect(page.getByText("Điều chỉnh mốc khảo sát")).toBeVisible();
  const toggle = page.getByRole("button", { name: "Chi tiết" });
  if (await toggle.isVisible()) {
    await toggle.click();
  }
}

test.describe("Kế hoạch và tiến độ: cập nhật mốc, task, ghi chú", () => {
  test("PM thêm task con và thấy task trong danh sách", async ({ page }) => {
    // Arrange
    const state: TaskState = { tasks: [], postedTasks: [] };
    await openSchedule(page, "PM", "PM", state);
    await expandMilestone(page);

    // Act
    await page.getByLabel("Tên task").fill(TASK_NAME);
    await page.getByRole("button", { name: "Thêm task" }).click();

    // Assert
    await expect(page.getByText(TASK_NAME)).toBeVisible();
    expect(state.postedTasks[0]?.name).toBe(TASK_NAME);
  });

  test("TVGS không thấy form sửa mốc nhưng thêm được ghi chú", async ({ page }) => {
    // Arrange
    const state: TaskState = { tasks: [], postedTasks: [] };

    // Act
    await openSchedule(page, "SUPERVISION_CONSULTANT", "SUPERVISION_CONSULTANT", state);
    await expandMilestone(page);

    // Assert
    await expect(page.getByRole("form", { name: "Sửa mốc M1" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Thêm ghi chú" })).toBeVisible();
  });
});

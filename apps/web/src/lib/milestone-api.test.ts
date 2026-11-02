import { describe, expect, it, vi } from "vitest";

import {
  createNote,
  createTask,
  deleteTask,
  fetchMyProjectRole,
  updateMilestone,
  updateTask,
} from "./milestone-api";

const BASE_URL = "http://api.test";
const PROJECT_ID = "project-1";
const MILESTONE_ID = "milestone-1";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("updateMilestone", () => {
  it("sends a PATCH with the bearer token and returns the updated milestone", async () => {
    // Arrange
    const fetchImpl = vi.fn(async () => jsonResponse({ id: MILESTONE_ID, progress_percent: "50" }));
    const payload = { progress_percent: 50, status: "IN_PROGRESS" as const };

    // Act
    await updateMilestone(PROJECT_ID, MILESTONE_ID, payload, "token-1", fetchImpl, BASE_URL);

    // Assert
    const [url, init] = fetchImpl.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe(`${BASE_URL}/api/v1/projects/${PROJECT_ID}/milestones/${MILESTONE_ID}`);
    expect(init.method).toBe("PATCH");
    expect(init.headers).toEqual({
      Authorization: "Bearer token-1",
      "Content-Type": "application/json",
    });
    expect(JSON.parse(init.body as string)).toEqual(payload);
  });

  it("throws the API detail message in Vietnamese when the rule is violated", async () => {
    // Arrange
    const fetchImpl = vi.fn(async () =>
      jsonResponse({ detail: "Chưa thể hoàn thành mốc" }, 422),
    );

    // Act
    const call = updateMilestone(PROJECT_ID, MILESTONE_ID, { status: "COMPLETED" }, "t", fetchImpl, BASE_URL);

    // Assert
    await expect(call).rejects.toThrow("Chưa thể hoàn thành mốc");
  });
});

describe("task and note writes", () => {
  it("creates a task under the milestone", async () => {
    // Arrange
    const fetchImpl = vi.fn(async () => jsonResponse({ id: "task-1", name: "Khảo sát" }, 201));

    // Act
    await createTask(
      PROJECT_ID,
      MILESTONE_ID,
      { name: "Khảo sát", status: "NOT_STARTED", assignee: null, due_date: null, note: null },
      "token-1",
      fetchImpl,
      BASE_URL,
    );

    // Assert
    const [url, init] = fetchImpl.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe(
      `${BASE_URL}/api/v1/projects/${PROJECT_ID}/milestones/${MILESTONE_ID}/tasks`,
    );
    expect(init.method).toBe("POST");
  });

  it("updates a task status with PATCH on the task URL", async () => {
    // Arrange
    const fetchImpl = vi.fn(async () => jsonResponse({ id: "task-1", status: "COMPLETED" }));

    // Act
    await updateTask(PROJECT_ID, MILESTONE_ID, "task-1", { status: "COMPLETED" }, "t", fetchImpl, BASE_URL);

    // Assert
    const [url, init] = fetchImpl.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toMatch(/\/tasks\/task-1$/);
    expect(init.method).toBe("PATCH");
  });

  it("deletes a task and resolves on 204", async () => {
    // Arrange
    const fetchImpl = vi.fn(async () => new Response(null, { status: 204 }));

    // Act
    await deleteTask(PROJECT_ID, MILESTONE_ID, "task-1", "t", fetchImpl, BASE_URL);

    // Assert
    const [, init] = fetchImpl.mock.calls[0] as unknown as [string, RequestInit];
    expect(init.method).toBe("DELETE");
  });

  it("posts a note body to the milestone notes URL", async () => {
    // Arrange
    const fetchImpl = vi.fn(async () => jsonResponse({ id: "note-1", body: "Đã khảo sát" }, 201));

    // Act
    await createNote(PROJECT_ID, MILESTONE_ID, "Đã khảo sát", "t", fetchImpl, BASE_URL);

    // Assert
    const [url, init] = fetchImpl.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toMatch(/\/notes$/);
    expect(JSON.parse(init.body as string)).toEqual({ body: "Đã khảo sát" });
  });
});

describe("fetchMyProjectRole", () => {
  it("returns the membership role of the user whose id matches the token subject", async () => {
    // Arrange
    const fetchImpl = vi.fn(async () =>
      jsonResponse([
        { user_id: "user-2", role: "PM" },
        { user_id: "user-1", role: "SUPERVISION_CONSULTANT" },
      ]),
    );

    // Act
    const role = await fetchMyProjectRole(PROJECT_ID, "user-1", "t", fetchImpl, BASE_URL);

    // Assert
    expect(role).toBe("SUPERVISION_CONSULTANT");
  });

  it("returns null when the user is not in the member list", async () => {
    // Arrange
    const fetchImpl = vi.fn(async () => jsonResponse([{ user_id: "user-2", role: "PM" }]));

    // Act
    const role = await fetchMyProjectRole(PROJECT_ID, "user-1", "t", fetchImpl, BASE_URL);

    // Assert
    expect(role).toBeNull();
  });
});

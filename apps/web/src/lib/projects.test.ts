import { describe, expect, it, vi } from "vitest";

import { fetchProjects } from "./projects";

const PROJECT_LIST = [
  {
    id: "p1",
    code: "SGD-HCM-CSVC-2026",
    name: "Xây dựng hệ thống quản lý dữ liệu",
    investor_name: "Sở GD&ĐT TP.HCM",
    decision_authority: null,
    total_investment: "5999498939.00",
    start_date: null,
    end_date: null,
  },
];

describe("fetchProjects", () => {
  it("sends the bearer token and returns the project list", async () => {
    // Arrange
    const fetchImpl = vi.fn(async () => new Response(JSON.stringify(PROJECT_LIST), { status: 200 }));

    // Act
    const projects = await fetchProjects("token-1", fetchImpl, "http://api.test");

    // Assert
    expect(projects).toEqual(PROJECT_LIST);
    expect(fetchImpl).toHaveBeenCalledWith(
      "http://api.test/api/v1/projects",
      expect.objectContaining({ headers: { Authorization: "Bearer token-1" } }),
    );
  });

  it("throws a Vietnamese error when the API responds with a failure status", async () => {
    // Arrange
    const fetchImpl = vi.fn(async () => new Response("{}", { status: 401 }));

    // Act
    const act = fetchProjects("token-1", fetchImpl, "http://api.test");

    // Assert
    await expect(act).rejects.toThrow("Không tải được danh sách dự án (mã 401)");
  });

  it("throws when the payload is not an array", async () => {
    // Arrange
    const fetchImpl = vi.fn(async () => new Response(JSON.stringify({ items: [] }), { status: 200 }));

    // Act
    const act = fetchProjects("token-1", fetchImpl, "http://api.test");

    // Assert
    await expect(act).rejects.toThrow("Dữ liệu danh sách dự án không hợp lệ");
  });
});

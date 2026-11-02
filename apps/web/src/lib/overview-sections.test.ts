import { describe, expect, it, vi } from "vitest";

import { fetchOverviewSections, formatDateVi } from "./overview-sections";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("formatDateVi", () => {
  it("formats an ISO date as dd/mm/yyyy without timezone shift", () => {
    // Arrange
    const isoDate = "2026-08-24";

    // Act
    const formatted = formatDateVi(isoDate);

    // Assert
    expect(formatted).toBe("24/08/2026");
  });

  it("returns null when the date is missing", () => {
    // Act
    const formatted = formatDateVi(null);

    // Assert
    expect(formatted).toBeNull();
  });
});

describe("fetchOverviewSections", () => {
  it("loads budget items and technical requirements with the bearer token", async () => {
    // Arrange
    const fetchImpl = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse([{ category: "SOFTWARE" }]))
      .mockResolvedValueOnce(jsonResponse([{ item: "Quy mô đối tượng" }]));

    // Act
    const sections = await fetchOverviewSections("p1", "token-abc", fetchImpl, "http://api.test");

    // Assert
    expect(sections.budgetItems).toEqual([{ category: "SOFTWARE" }]);
    expect(sections.requirements).toEqual([{ item: "Quy mô đối tượng" }]);
    const urls = fetchImpl.mock.calls.map(([url]) => url);
    expect(urls).toEqual([
      "http://api.test/api/v1/projects/p1/budget-items",
      "http://api.test/api/v1/projects/p1/technical-requirements",
    ]);
    for (const [, init] of fetchImpl.mock.calls) {
      expect(init?.headers).toEqual({ Authorization: "Bearer token-abc" });
    }
  });

  it("throws with the HTTP status when a request fails", async () => {
    // Arrange
    const fetchImpl = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse([]))
      .mockResolvedValueOnce(jsonResponse({}, 500));

    // Act & Assert
    await expect(
      fetchOverviewSections("p1", "token-abc", fetchImpl, "http://api.test"),
    ).rejects.toThrow("mã 500");
  });
});

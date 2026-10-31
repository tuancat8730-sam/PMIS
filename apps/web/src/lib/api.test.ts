import { describe, expect, it } from "vitest";

import { DEFAULT_API_URL, fetchApiHealth, resolveApiUrl } from "./api";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("resolveApiUrl", () => {
  it("uses the default base URL when none is configured", () => {
    expect(resolveApiUrl("/api/v1/health", undefined)).toBe(
      `${DEFAULT_API_URL}/api/v1/health`,
    );
  });

  it("strips trailing slashes from the base URL and leading slashes from the path", () => {
    expect(resolveApiUrl("api/v1/health", "https://api.example.gov.vn//")).toBe(
      "https://api.example.gov.vn/api/v1/health",
    );
  });
});

describe("fetchApiHealth", () => {
  it("returns ok when the API reports status ok", async () => {
    // Arrange
    const fakeFetch = async () => jsonResponse({ status: "ok" });

    // Act
    const status = await fetchApiHealth(fakeFetch);

    // Assert
    expect(status).toBe("ok");
  });

  it("returns unreachable when the network request fails", async () => {
    // Arrange
    const fakeFetch = async () => {
      throw new TypeError("fetch failed");
    };

    // Act
    const status = await fetchApiHealth(fakeFetch);

    // Assert
    expect(status).toBe("unreachable");
  });

  it("returns unreachable when the API answers with an error status", async () => {
    // Arrange
    const fakeFetch = async () => jsonResponse({ status: "ok" }, 503);

    // Act
    const status = await fetchApiHealth(fakeFetch);

    // Assert
    expect(status).toBe("unreachable");
  });

  it("returns unreachable when the body does not match the health contract", async () => {
    // Arrange
    const fakeFetch = async () => jsonResponse({ unexpected: true });

    // Act
    const status = await fetchApiHealth(fakeFetch);

    // Assert
    expect(status).toBe("unreachable");
  });
});

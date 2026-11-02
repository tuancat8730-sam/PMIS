import { describe, expect, it } from "vitest";

import { LOGIN_PATH, parseLoginInput, requestLoginToken } from "./auth";

const BASE_URL = "https://api.example.gov.vn";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("parseLoginInput", () => {
  it("accepts a valid email and a non-empty password", () => {
    // Arrange
    const raw = { email: "ban@example.com", password: "secret-123" };

    // Act
    const result = parseLoginInput(raw);

    // Assert
    expect(result.success).toBe(true);
  });

  it("rejects an email that is not a valid address", () => {
    // Arrange
    const raw = { email: "khong-phai-email", password: "secret-123" };

    // Act
    const result = parseLoginInput(raw);

    // Assert
    expect(result.success).toBe(false);
  });

  it("rejects an empty password", () => {
    // Arrange
    const raw = { email: "ban@example.com", password: "" };

    // Act
    const result = parseLoginInput(raw);

    // Assert
    expect(result.success).toBe(false);
  });
});

describe("requestLoginToken", () => {
  const INPUT = { email: "ban@example.com", password: "secret-123" };

  it("posts form-encoded credentials to the login endpoint and returns the access token", async () => {
    // Arrange
    let capturedUrl = "";
    let capturedInit: RequestInit | undefined;
    const fakeFetch = async (url: string | URL | Request, init?: RequestInit) => {
      capturedUrl = String(url);
      capturedInit = init;
      return jsonResponse({ access_token: "jwt-abc", token_type: "bearer", role: "ADMIN" });
    };

    // Act
    const token = await requestLoginToken(INPUT, fakeFetch, BASE_URL);

    // Assert
    expect(token).toBe("jwt-abc");
    expect(capturedUrl).toBe(`${BASE_URL}${LOGIN_PATH}`);
    expect(capturedInit?.method).toBe("POST");
    const sentBody = new URLSearchParams(String(capturedInit?.body));
    expect(sentBody.get("username")).toBe("ban@example.com");
    expect(sentBody.get("password")).toBe("secret-123");
  });

  it("shows the API detail message when credentials are wrong", async () => {
    // Arrange
    const fakeFetch = async () =>
      jsonResponse({ detail: "Email hoặc mật khẩu không đúng" }, 401);

    // Act & Assert
    await expect(requestLoginToken(INPUT, fakeFetch, BASE_URL)).rejects.toThrow(
      "Email hoặc mật khẩu không đúng",
    );
  });

  it("shows a rate-limit message when the API answers 429", async () => {
    // Arrange
    const fakeFetch = async () =>
      jsonResponse({ detail: "Bạn thao tác quá nhiều lần, vui lòng thử lại sau" }, 429);

    // Act & Assert
    await expect(requestLoginToken(INPUT, fakeFetch, BASE_URL)).rejects.toThrow(
      "Bạn thao tác quá nhiều lần, vui lòng thử lại sau",
    );
  });

  it("shows a connection message when the network request fails", async () => {
    // Arrange
    const fakeFetch = async () => {
      throw new TypeError("fetch failed");
    };

    // Act & Assert
    await expect(requestLoginToken(INPUT, fakeFetch, BASE_URL)).rejects.toThrow(
      "Không kết nối được máy chủ",
    );
  });

  it("rejects when the success body does not contain an access token", async () => {
    // Arrange
    const fakeFetch = async () => jsonResponse({ unexpected: true });

    // Act & Assert
    await expect(requestLoginToken(INPUT, fakeFetch, BASE_URL)).rejects.toThrow(
      "Phản hồi đăng nhập không hợp lệ",
    );
  });
});

import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { LoginForm } from "./login-form";

describe("LoginForm", () => {
  it("renders Vietnamese email and password fields with a submit button", () => {
    // Arrange & Act
    const markup = renderToStaticMarkup(<LoginForm onLoggedIn={() => undefined} />);

    // Assert
    expect(markup).toContain('type="email"');
    expect(markup).toContain('type="password"');
    expect(markup).toContain("Email");
    expect(markup).toContain("Mật khẩu");
    expect(markup).toContain("Đăng nhập");
  });

  it("does not show an error before the user submits", () => {
    // Arrange & Act
    const markup = renderToStaticMarkup(<LoginForm onLoggedIn={() => undefined} />);

    // Assert
    expect(markup).not.toContain('role="alert"');
  });
});

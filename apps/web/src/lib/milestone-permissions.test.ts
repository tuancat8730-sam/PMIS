import { describe, expect, it } from "vitest";

import {
  canEditMilestoneFields,
  canWriteTasksAndNotes,
  effectiveProjectRole,
  readTokenClaims,
} from "./milestone-permissions";

function tokenWithPayload(payload: Record<string, unknown>): string {
  return ["header", btoa(JSON.stringify(payload)), "signature"].join(".");
}

describe("readTokenClaims", () => {
  it("reads subject and global role from the JWT payload", () => {
    // Arrange
    const token = tokenWithPayload({ sub: "user-1", role: "PM" });

    // Act
    const claims = readTokenClaims(token);

    // Assert
    expect(claims).toEqual({ subject: "user-1", role: "PM" });
  });

  it("returns null for a token that is not three segments", () => {
    // Arrange
    const token = "khong-phai-jwt";

    // Act
    const claims = readTokenClaims(token);

    // Assert
    expect(claims).toBeNull();
  });

  it("returns null when the payload is not valid JSON", () => {
    // Arrange
    const token = ["header", "%%%", "signature"].join(".");

    // Act
    const claims = readTokenClaims(token);

    // Assert
    expect(claims).toBeNull();
  });
});

describe("effectiveProjectRole", () => {
  it("gives ADMIN full access regardless of membership", () => {
    // Arrange
    const claims = { subject: "user-1", role: "ADMIN" };

    // Act
    const role = effectiveProjectRole(claims, "INVESTOR");

    // Assert
    expect(role).toBe("ADMIN");
  });

  it("uses the project membership role for non-admin users", () => {
    // Arrange
    const claims = { subject: "user-1", role: "PM" };

    // Act
    const role = effectiveProjectRole(claims, "SUPERVISION_CONSULTANT");

    // Assert
    expect(role).toBe("SUPERVISION_CONSULTANT");
  });

  it("returns null when the user is not a project member", () => {
    // Arrange
    const claims = { subject: "user-1", role: "PM" };

    // Act
    const role = effectiveProjectRole(claims, null);

    // Assert
    expect(role).toBeNull();
  });
});

describe("canEditMilestoneFields", () => {
  it.each([
    ["PM", true],
    ["ADMIN", true],
    ["SUPERVISION_CONSULTANT", false],
    ["INVESTOR", false],
    [null, false],
  ])("returns true only for PM and ADMIN when role is %s", (role, expected) => {
    // Arrange / Act
    const allowed = canEditMilestoneFields(role);

    // Assert
    expect(allowed).toBe(expected);
  });
});

describe("canWriteTasksAndNotes", () => {
  it.each([
    ["PM", true],
    ["SUPERVISION_CONSULTANT", true],
    ["ADMIN", true],
    ["INVESTOR", false],
    ["CONTRACTOR", false],
    [null, false],
  ])("returns true for PM, TVGS and ADMIN only when role is %s", (role, expected) => {
    // Arrange / Act
    const allowed = canWriteTasksAndNotes(role);

    // Assert
    expect(allowed).toBe(expected);
  });
});

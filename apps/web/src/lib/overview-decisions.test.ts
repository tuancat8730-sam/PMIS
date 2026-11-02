import { describe, expect, it } from "vitest";

import { groupDecisionsByKind, type LegalDecisionRow } from "./overview";

function makeDecision(overrides: Partial<LegalDecisionRow>): LegalDecisionRow {
  return {
    id: "d1",
    kind: "PROJECT_APPROVAL",
    decision_no: "1595/QĐ-SGDĐT",
    decision_date: "2026-05-22",
    issuing_authority: "Sở GD&ĐT TP.HCM",
    amount: null,
    funding_source: null,
    execution_period: null,
    note: null,
    ...overrides,
  };
}

describe("groupDecisionsByKind", () => {
  it("lists the project approval group first and skips kinds without decisions", () => {
    // Arrange
    const supervision = makeDecision({ id: "d2", kind: "SUPERVISION_ASSIGNMENT" });
    const approval = makeDecision({ id: "d1", kind: "PROJECT_APPROVAL" });

    // Act
    const groups = groupDecisionsByKind([supervision, approval]);

    // Assert
    expect(groups.map((group) => group.kind)).toEqual([
      "PROJECT_APPROVAL",
      "SUPERVISION_ASSIGNMENT",
    ]);
    expect(groups[0].rows).toEqual([approval]);
  });

  it("returns no groups for an empty list", () => {
    // Act
    const groups = groupDecisionsByKind([]);

    // Assert
    expect(groups).toEqual([]);
  });
});

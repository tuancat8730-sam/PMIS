import { describe, expect, it } from "vitest";

import { buildRiskHeatmap, riskCellTone, sortRisksByScore } from "./risk-heatmap";
import type { RiskRow } from "./tracking";

function makeRisk(overrides: Partial<RiskRow>): RiskRow {
  return {
    id: "r1",
    code: "R1",
    record_type: "RISK",
    title: "Dữ liệu nguồn chậm",
    status: "OPEN",
    owner: null,
    due_date: null,
    impact: "HIGH",
    likelihood: "VERY_HIGH",
    score: 12,
    coordinating_units: null,
    ...overrides,
  };
}

describe("buildRiskHeatmap", () => {
  it("places each assessed risk in the cell for its impact and likelihood", () => {
    // Arrange
    const risk = makeRisk({ id: "r1", impact: "HIGH", likelihood: "VERY_HIGH" });

    // Act
    const heatmap = buildRiskHeatmap([risk]);

    // Assert
    const cell = heatmap.cells.find(
      (candidate) => candidate.impact === "HIGH" && candidate.likelihood === "VERY_HIGH",
    );
    expect(cell?.rows).toEqual([risk]);
  });

  it("returns all sixteen cells even when no risk falls into them", () => {
    // Arrange
    const risks: RiskRow[] = [];

    // Act
    const heatmap = buildRiskHeatmap(risks);

    // Assert
    expect(heatmap.cells).toHaveLength(16);
    expect(heatmap.cells.every((cell) => cell.rows.length === 0)).toBe(true);
  });

  it("collects risks missing impact or likelihood under unassessed", () => {
    // Arrange
    const noImpact = makeRisk({ id: "r1", impact: null });
    const noLikelihood = makeRisk({ id: "r2", likelihood: null });
    const assessed = makeRisk({ id: "r3" });

    // Act
    const heatmap = buildRiskHeatmap([noImpact, noLikelihood, assessed]);

    // Assert
    expect(heatmap.unassessed).toEqual([noImpact, noLikelihood]);
    expect(heatmap.cells.flatMap((cell) => cell.rows)).toEqual([assessed]);
  });

  it("does not mutate the input array", () => {
    // Arrange
    const risks = [makeRisk({ id: "r1" }), makeRisk({ id: "r2", impact: null })];
    const snapshot = [...risks];

    // Act
    buildRiskHeatmap(risks);

    // Assert
    expect(risks).toEqual(snapshot);
  });
});

describe("riskCellTone", () => {
  it("rates the LOW impact with LOW likelihood cell as low", () => {
    // Act
    const tone = riskCellTone("LOW", "LOW");

    // Assert
    expect(tone).toBe("low");
  });

  it("rates the VERY_HIGH impact with VERY_HIGH likelihood cell as critical", () => {
    // Act
    const tone = riskCellTone("VERY_HIGH", "VERY_HIGH");

    // Assert
    expect(tone).toBe("critical");
  });

  it("rates a cell by the product of its two levels", () => {
    // Act and Assert
    expect(riskCellTone("MEDIUM", "HIGH")).toBe("medium");
    expect(riskCellTone("HIGH", "HIGH")).toBe("high");
  });
});

describe("sortRisksByScore", () => {
  it("sorts by score descending and puts unscored risks last", () => {
    // Arrange
    const low = makeRisk({ id: "low", score: 3 });
    const high = makeRisk({ id: "high", score: 16 });
    const unscored = makeRisk({ id: "none", score: null });

    // Act
    const sorted = sortRisksByScore([low, unscored, high]);

    // Assert
    expect(sorted.map((risk) => risk.id)).toEqual(["high", "low", "none"]);
  });

  it("returns a new array and keeps the input order", () => {
    // Arrange
    const first = makeRisk({ id: "first", score: 1 });
    const second = makeRisk({ id: "second", score: 9 });
    const input = [first, second];

    // Act
    const sorted = sortRisksByScore(input);

    // Assert
    expect(sorted).not.toBe(input);
    expect(input).toEqual([first, second]);
  });
});

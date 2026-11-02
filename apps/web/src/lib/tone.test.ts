import { describe, expect, it } from "vitest";

import { legalStatusTone, milestoneStatusTone, riskLevelTone } from "./tone";

describe("riskLevelTone", () => {
  it("maps an unassessed risk level to the neutral tone", () => {
    // Arrange
    const level = null;

    // Act
    const tone = riskLevelTone(level);

    // Assert
    expect(tone).toBe("neutral");
  });

  it("maps VERY_HIGH to the critical tone and LOW to the low tone", () => {
    // Act and Assert
    expect(riskLevelTone("VERY_HIGH")).toBe("critical");
    expect(riskLevelTone("LOW")).toBe("low");
  });
});

describe("milestoneStatusTone", () => {
  it("maps OVERDUE to the critical tone", () => {
    // Act
    const tone = milestoneStatusTone("OVERDUE");

    // Assert
    expect(tone).toBe("critical");
  });

  it("maps COMPLETED to the low tone", () => {
    // Act
    const tone = milestoneStatusTone("COMPLETED");

    // Assert
    expect(tone).toBe("low");
  });
});

describe("legalStatusTone", () => {
  it("maps MISSING and DISCREPANCY_FOUND to distinct warning tones", () => {
    // Act
    const missing = legalStatusTone("MISSING");
    const discrepancy = legalStatusTone("DISCREPANCY_FOUND");

    // Assert
    expect(missing).not.toBe(discrepancy);
    expect(discrepancy).toBe("critical");
  });

  it("maps VERIFIED_CLOSED to the low tone", () => {
    // Act
    const tone = legalStatusTone("VERIFIED_CLOSED");

    // Assert
    expect(tone).toBe("low");
  });
});

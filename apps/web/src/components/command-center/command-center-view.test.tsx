import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { CommandCenterView } from "./command-center-view";
import type { CommandCenterData } from "@/lib/command-center";

const DATA: CommandCenterData = {
  as_of: "2026-11-01",
  kpi: {
    contract_value_by_kind: { MAIN: "111070000000.00", CONSULTING: "1120000000.00" },
    contract_value_total: "112190000000.00",
    running_project_count: 2,
    beneficiary_unit_count: 10,
    pending_signature_count: null,
    red_alert_count: 1,
  },
  projects: [
    { id: "1", code: "CC-A", short_name: "A", health: "AT_RISK", red_alert_count: 1, max_slippage_days: 3 },
    { id: "2", code: "CC-B", short_name: "B", health: "CRITICAL", red_alert_count: 0, max_slippage_days: 9 },
  ],
  red_alerts: [
    { project_code: "CC-A", source: "MILESTONE", code: "M1", title: "Mốc khẩn 1", due_date: "2026-11-02" },
  ],
  contract_countdowns: [],
};

function render(selectedCode: string | null): string {
  return renderToStaticMarkup(
    <CommandCenterView data={DATA} selectedCode={selectedCode} onSelectProject={() => undefined} />,
  );
}

describe("CommandCenterView", () => {
  it("shows the pending-signature KPI as 'chưa có dữ liệu' instead of a fake number", () => {
    // Act
    const html = render(null);

    // Assert
    expect(html).toContain("chưa có dữ liệu");
  });

  it("renders red alert cards from the data", () => {
    // Act
    const html = render(null);

    // Assert
    expect(html).toContain("Mốc khẩn 1");
  });

  it("hides rows of other projects when a project is selected", () => {
    // Act
    const html = render("CC-B");

    // Assert
    expect(html).not.toContain("Mốc khẩn 1");
    expect(html).toContain("CC-B");
  });
});

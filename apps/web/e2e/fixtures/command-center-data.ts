import type { CommandCenterData } from "../../src/lib/command-center";

/** Dữ liệu giả lập cho E2E. Hình dạng khớp đúng với API `GET /api/v1/command-center`. */
export const COMMAND_CENTER_FIXTURE: CommandCenterData = {
  as_of: "2026-11-01",
  kpi: {
    contract_value_by_kind: { MAIN: "111070000000.00", CONSULTING: "1120000000.00" },
    contract_value_total: "112190000000.00",
    running_project_count: 2,
    beneficiary_unit_count: 10,
    pending_signature_count: null,
    red_alert_count: 2,
  },
  projects: [
    {
      id: "11111111-1111-1111-1111-111111111111",
      code: "CC-A",
      short_name: "Dự án A",
      health: "AT_RISK",
      red_alert_count: 1,
      max_slippage_days: 3,
    },
    {
      id: "22222222-2222-2222-2222-222222222222",
      code: "CC-B",
      short_name: "Dự án B",
      health: "CRITICAL",
      red_alert_count: 1,
      max_slippage_days: 9,
    },
  ],
  red_alerts: [
    {
      project_code: "CC-A",
      source: "MILESTONE",
      code: "M1",
      title: "Mốc khẩn A",
      due_date: "2026-11-02",
    },
    {
      project_code: "CC-B",
      source: "RISK",
      code: "R1",
      title: "Rủi ro khẩn B",
      due_date: "2026-10-30",
    },
  ],
  contract_countdowns: [
    {
      project_code: "CC-B",
      contract_number: "29/HĐKT",
      status: "WARNING",
      expiration_date: "2026-11-20",
      days_remaining: 19,
    },
  ],
};

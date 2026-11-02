import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { ContractsView } from "./contracts-view";
import type { ContractSummaryRow } from "../../lib/overview";

const CONTRACT: ContractSummaryRow = {
  id: "c1",
  package_name: "Gói triển khai",
  package_kind: "IMPLEMENTATION",
  contract_number: "29/HĐKT-DVN",
  signed_date: "2026-09-21",
  expiration_date: null,
  contract_value: "4848186000.00",
  contractor_name: null,
  role_label: null,
  contact_person: null,
  status_note: null,
};

describe("ContractsView", () => {
  it("shows the package name, contract number and signed date", () => {
    // Act
    const markup = renderToStaticMarkup(<ContractsView contracts={[CONTRACT]} />);

    // Assert
    expect(markup).toContain("Gói triển khai");
    expect(markup).toContain("29/HĐKT-DVN");
    expect(markup).toContain("21/09/2026");
  });

  it("shows the contract value formatted in vi-VN", () => {
    // Act
    const markup = renderToStaticMarkup(<ContractsView contracts={[CONTRACT]} />);

    // Assert
    expect(markup).toContain("4.848.186.000 đ");
  });

  it("shows an empty message when there are no contracts", () => {
    // Act
    const markup = renderToStaticMarkup(<ContractsView contracts={[]} />);

    // Assert
    expect(markup).toContain("Chưa có hợp đồng nào");
  });
});

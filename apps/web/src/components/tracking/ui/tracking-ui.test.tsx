import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { EmptyState } from "./empty-state";
import { Field } from "./field";
import { ProgressBar } from "./progress-bar";
import { StatCard } from "./stat-card";
import { StatusChip } from "./status-chip";

describe("StatusChip", () => {
  it("renders the label with the classes of its tone", () => {
    // Arrange / Act
    const html = renderToStaticMarkup(<StatusChip tone="critical" label="Quá hạn" />);

    // Assert
    expect(html).toContain("Quá hạn");
    expect(html).toContain("bg-tone-critical-bg");
  });
});

describe("ProgressBar", () => {
  it("clamps values above 100 to 100", () => {
    // Arrange / Act
    const html = renderToStaticMarkup(<ProgressBar label="Tiến độ" percent={150} />);

    // Assert
    expect(html).toContain('aria-valuenow="100"');
    expect(html).toContain("width:100%");
  });

  it("clamps negative values to 0", () => {
    // Arrange / Act
    const html = renderToStaticMarkup(<ProgressBar label="Tiến độ" percent={-5} />);

    // Assert
    expect(html).toContain('aria-valuenow="0"');
  });
});

describe("StatCard", () => {
  it("renders the label, the value and the optional hint", () => {
    // Arrange / Act
    const html = renderToStaticMarkup(
      <StatCard label="Rủi ro mở" value="7" hint="Trong 30 ngày" />,
    );

    // Assert
    expect(html).toContain("Rủi ro mở");
    expect(html).toContain("7");
    expect(html).toContain("Trong 30 ngày");
  });
});

describe("Field", () => {
  it("shows the default missing text instead of guessing when the value is null", () => {
    // Arrange / Act
    const html = renderToStaticMarkup(<Field label="Ghi chú PM" value={null} />);

    // Assert
    expect(html).toContain("Chưa có thông tin");
  });

  it("shows the given value when it is present", () => {
    // Arrange / Act
    const html = renderToStaticMarkup(<Field label="Ghi chú PM" value="Chờ serial" />);

    // Assert
    expect(html).toContain("Chờ serial");
    expect(html).not.toContain("Chưa có thông tin");
  });
});

describe("EmptyState", () => {
  it("renders the message it receives", () => {
    // Arrange / Act
    const html = renderToStaticMarkup(<EmptyState message="Chưa có file nào" />);

    // Assert
    expect(html).toContain("Chưa có file nào");
  });
});

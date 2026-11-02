import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { DriveSyncBar } from "./drive-sync-bar";

describe("DriveSyncBar", () => {
  it("shows the last sync time and a scan-now button", () => {
    // Act
    const markup = renderToStaticMarkup(
      <DriveSyncBar lastSyncedAt="2026-11-02T08:00:00Z" syncing={false} message={null} onSync={() => {}} />,
    );

    // Assert
    expect(markup).toContain("Cập nhật lúc");
    expect(markup).toContain("Quét ngay");
    expect(markup).not.toContain("disabled");
  });

  it("says nothing has been synced when there is no sync time", () => {
    // Act
    const markup = renderToStaticMarkup(
      <DriveSyncBar lastSyncedAt={null} syncing={false} message={null} onSync={() => {}} />,
    );

    // Assert
    expect(markup).toContain("Chưa đồng bộ lần nào");
  });

  it("disables the button and shows progress while scanning", () => {
    // Act
    const markup = renderToStaticMarkup(
      <DriveSyncBar lastSyncedAt={null} syncing={true} message={null} onSync={() => {}} />,
    );

    // Assert
    expect(markup).toContain("Đang quét");
    expect(markup).toContain("disabled");
  });

  it("shows the result message as a status line", () => {
    // Act
    const markup = renderToStaticMarkup(
      <DriveSyncBar
        lastSyncedAt={null}
        syncing={false}
        message="Đã quét: 3 file"
        onSync={() => {}}
      />,
    );

    // Assert
    expect(markup).toContain('role="status"');
    expect(markup).toContain("Đã quét: 3 file");
  });
});

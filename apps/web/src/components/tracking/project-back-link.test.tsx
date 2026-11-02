import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { ProjectBackLink } from "./project-back-link";

describe("ProjectBackLink", () => {
  it("links back to the projects list with a Vietnamese label", () => {
    // Act
    const markup = renderToStaticMarkup(<ProjectBackLink />);

    // Assert
    expect(markup).toContain('href="/projects"');
    expect(markup).toContain("Quay lại danh sách dự án");
  });
});

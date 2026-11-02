import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { ProjectHomeView } from "./project-home-view";
import { PROJECT_SECTIONS } from "./project-sections";
import { ProjectListView } from "./project-list-view";
import type { ProjectOverview, ProjectSummary } from "../../lib/overview";

const PROJECT: ProjectSummary = {
  id: "p1",
  code: "SGD-HCM-CSVC-2026",
  name: "Xây dựng hệ thống quản lý dữ liệu",
  investor_name: "Sở GD&ĐT TP.HCM",
  decision_authority: null,
  total_investment: "5999498939.00",
  start_date: null,
  end_date: null,
};

describe("ProjectHomeView", () => {
  it("links every tracking section to its own route", () => {
    // Arrange
    const overview: ProjectOverview = { project: PROJECT, decisions: [], contracts: [] };

    // Act
    const html = renderToStaticMarkup(<ProjectHomeView overview={overview} />);

    // Assert
    expect(html).toContain('href="/projects/p1/overview"');
    expect(html).toContain('href="/projects/p1/schedule"');
    expect(html).toContain('href="/projects/p1/risks"');
    expect(html).toContain('href="/projects/p1/legal"');
    expect(html).toContain('href="/projects/p1/files"');
    expect(html).toContain('href="/projects/p1/decisions"');
    expect(html).toContain('href="/projects/p1/contracts"');
  });

  it("lists the overview first, then the six Excel sheets, then the Drive files tab", () => {
    // Arrange
    const expectedLabels = [
      "Tổng quan",
      "Mốc",
      "Rủi ro",
      "Pháp lý",
      "File",
      "Tệp Drive",
      "Quyết định",
      "Hợp đồng",
    ];

    // Act
    const labels = PROJECT_SECTIONS.map((section) => section.label);

    // Assert
    expect(labels).toEqual(expectedLabels);
  });

  it("shows the project name and code", () => {
    // Arrange
    const overview: ProjectOverview = { project: PROJECT, decisions: [], contracts: [] };

    // Act
    const html = renderToStaticMarkup(<ProjectHomeView overview={overview} />);

    // Assert
    expect(html).toContain("Xây dựng hệ thống quản lý dữ liệu");
    expect(html).toContain("SGD-HCM-CSVC-2026");
  });
});

describe("ProjectListView", () => {
  it("links each project to its home page", () => {
    // Arrange
    const projects = [PROJECT, { ...PROJECT, id: "p2", code: "SGD-LD-TB10-2026" }];

    // Act
    const html = renderToStaticMarkup(<ProjectListView projects={projects} />);

    // Assert
    expect(html).toContain('href="/projects/p1"');
    expect(html).toContain('href="/projects/p2"');
    expect(html).toContain("SGD-LD-TB10-2026");
  });

  it("shows an empty-state message when there are no projects", () => {
    // Arrange
    const projects: ProjectSummary[] = [];

    // Act
    const html = renderToStaticMarkup(<ProjectListView projects={projects} />);

    // Assert
    expect(html).toContain("Chưa có dự án nào");
  });
});

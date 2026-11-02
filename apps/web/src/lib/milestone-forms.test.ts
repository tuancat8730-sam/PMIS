import { describe, expect, it } from "vitest";

import {
  parseMilestoneEdit,
  parseTaskForm,
  taskProgressLabel,
  type MilestoneEditInput,
} from "./milestone-forms";

const UNLOCKED_CONTEXT = { locked: false, currentAdjustedEnd: null } as const;
const LOCKED_CONTEXT = { locked: true, currentAdjustedEnd: "2026-11-30" } as const;

function editInput(overrides: Partial<MilestoneEditInput> = {}): MilestoneEditInput {
  return {
    adjustedEnd: "",
    actualEnd: "",
    progressPercent: "40",
    status: "IN_PROGRESS",
    reason: "",
    ...overrides,
  };
}

describe("parseMilestoneEdit", () => {
  it("accepts progress from 0 to 100 and converts empty dates to null", () => {
    // Arrange
    const input = editInput({ progressPercent: "100", adjustedEnd: "" });

    // Act
    const result = parseMilestoneEdit(input, UNLOCKED_CONTEXT);

    // Assert
    expect(result).toEqual({
      ok: true,
      value: {
        adjusted_end: null,
        actual_end: null,
        progress_percent: 100,
        status: "IN_PROGRESS",
      },
    });
  });

  it("rejects progress above 100 with a Vietnamese message", () => {
    // Arrange
    const input = editInput({ progressPercent: "101" });

    // Act
    const result = parseMilestoneEdit(input, UNLOCKED_CONTEXT);

    // Assert
    expect(result).toEqual({ ok: false, message: "Phần trăm hoàn thành phải từ 0 đến 100" });
  });

  it("rejects a non-numeric progress value", () => {
    // Arrange
    const input = editInput({ progressPercent: "abc" });

    // Act
    const result = parseMilestoneEdit(input, UNLOCKED_CONTEXT);

    // Assert
    expect(result.ok).toBe(false);
  });

  it("requires a reason when a locked milestone's adjusted end changes", () => {
    // Arrange
    const input = editInput({ adjustedEnd: "2026-12-05", reason: "  " });

    // Act
    const result = parseMilestoneEdit(input, LOCKED_CONTEXT);

    // Assert
    expect(result).toEqual({
      ok: false,
      message: "Thay đổi hạn của mốc đã khóa cần ghi lý do",
    });
  });

  it("sends the reason when a locked milestone's adjusted end changes", () => {
    // Arrange
    const input = editInput({ adjustedEnd: "2026-12-05", reason: "Có công văn gia hạn" });

    // Act
    const result = parseMilestoneEdit(input, LOCKED_CONTEXT);

    // Assert
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.value.reason).toBe("Có công văn gia hạn");
      expect(result.value.adjusted_end).toBe("2026-12-05");
    }
  });

  it("does not require a reason when the adjusted end is unchanged on a locked milestone", () => {
    // Arrange
    const input = editInput({ adjustedEnd: "2026-11-30", reason: "" });

    // Act
    const result = parseMilestoneEdit(input, LOCKED_CONTEXT);

    // Assert
    expect(result.ok).toBe(true);
  });

  it("rejects a malformed date", () => {
    // Arrange
    const input = editInput({ actualEnd: "30/11/2026" });

    // Act
    const result = parseMilestoneEdit(input, UNLOCKED_CONTEXT);

    // Assert
    expect(result).toEqual({ ok: false, message: "Ngày phải có dạng năm-tháng-ngày" });
  });
});

describe("parseTaskForm", () => {
  it("requires a task name", () => {
    // Arrange / Act
    const result = parseTaskForm({ name: "   ", status: "NOT_STARTED", assignee: "", dueDate: "", note: "" });

    // Assert
    expect(result).toEqual({ ok: false, message: "Tên task không được để trống" });
  });

  it("converts empty optional fields to null", () => {
    // Arrange / Act
    const result = parseTaskForm({
      name: "Khảo sát trường A",
      status: "COMPLETED",
      assignee: "",
      dueDate: "2026-11-20",
      note: "",
    });

    // Assert
    expect(result).toEqual({
      ok: true,
      value: {
        name: "Khảo sát trường A",
        status: "COMPLETED",
        assignee: null,
        due_date: "2026-11-20",
        note: null,
      },
    });
  });
});

describe("taskProgressLabel", () => {
  it("says there are no tasks when the list is empty", () => {
    // Arrange / Act
    const label = taskProgressLabel([]);

    // Assert
    expect(label).toBe("Chưa có task con");
  });

  it("counts completed tasks out of the total", () => {
    // Arrange
    const tasks = [{ status: "COMPLETED" }, { status: "IN_PROGRESS" }, { status: "COMPLETED" }];

    // Act
    const label = taskProgressLabel(tasks);

    // Assert
    expect(label).toBe("2/3 task xong");
  });
});

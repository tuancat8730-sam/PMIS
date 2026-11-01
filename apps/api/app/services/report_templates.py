"""Định nghĩa ba mẫu báo cáo E11 (dữ liệu thuần, không chạm DB).

Nguồn: `docs/report-samples/e11-sample-templates.md` (bản nháp, chưa đối chiếu thể thức NĐ 30/2020).
Khi có mẫu thật (Q1, Q2), sửa các danh sách dưới đây; không sửa logic xuất file.
"""

from dataclasses import dataclass
from enum import StrEnum


class ReportKind(StrEnum):
    PM_WEEKLY = "PM_WEEKLY"
    SUPERVISION_WEEKLY = "SUPERVISION_WEEKLY"
    MEETING_NOTE = "MEETING_NOTE"


@dataclass(frozen=True)
class TemplateSection:
    title: str
    placeholders: tuple[str, ...]


@dataclass(frozen=True)
class ReportTemplate:
    kind: ReportKind
    title: str
    sections: tuple[TemplateSection, ...]


_TEMPLATES: dict[ReportKind, ReportTemplate] = {
    ReportKind.PM_WEEKLY: ReportTemplate(
        kind=ReportKind.PM_WEEKLY,
        title="Báo cáo QLDA tuần",
        sections=(
            TemplateSection("Thông tin dự án", ("project.code", "project.name", "period")),
            TemplateSection(
                "Tiến độ mốc", ("milestones.done", "milestones.open", "milestones.late")
            ),
            TemplateSection("Rủi ro và vướng mắc", ("risks.open",)),
            TemplateSection("Hợp đồng", ("contract.number", "contract.value")),
            TemplateSection("Hồ sơ pháp lý", ("legal.pending",)),
            TemplateSection("Giao hàng, serial", ("serials.delivered", "serials.missing")),
            TemplateSection("Kiến nghị theo đối tượng", ("target",)),
            TemplateSection("Kế hoạch tuần tới", ("plan.next_week",)),
        ),
    ),
    ReportKind.SUPERVISION_WEEKLY: ReportTemplate(
        kind=ReportKind.SUPERVISION_WEEKLY,
        title="Báo cáo giám sát tuần",
        sections=(
            TemplateSection("Thông tin gói giám sát", ("project.code", "contract.number")),
            TemplateSection("Điểm dừng kiểm tra", ("hold.open", "hold.confirmed")),
            TemplateSection("Đơn vị thụ hưởng đã khảo sát", ("beneficiary.surveyed",)),
            TemplateSection("Vướng mắc tại hiện trường", ("risks.open",)),
            TemplateSection("Kết luận và kiến nghị", ()),
        ),
    ),
    ReportKind.MEETING_NOTE: ReportTemplate(
        kind=ReportKind.MEETING_NOTE,
        title="Meeting note giao ban",
        sections=(
            TemplateSection("Thời gian và thành phần", ("meeting.date", "meeting.attendees")),
            TemplateSection("Nội dung đã thảo luận", ("meeting.points",)),
            TemplateSection("Quyết định", ("meeting.decisions",)),
            TemplateSection("Việc cần làm", ("task.owner", "task.due", "task.content")),
        ),
    ),
}


def get_template(kind: ReportKind) -> ReportTemplate:
    return _TEMPLATES[kind]

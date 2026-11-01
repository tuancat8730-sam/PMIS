from io import BytesIO

import pytest
from app.services.report_templates import ReportKind, get_template
from docx import Document

from app.services.docx_generator import RenderedSection, render_report_docx

pytestmark = pytest.mark.unit


def _paragraph_texts(payload: bytes) -> list[str]:
    document = Document(BytesIO(payload))
    return [paragraph.text for paragraph in document.paragraphs]


def test_rendered_docx_contains_title_and_every_section_heading() -> None:
    # Arrange
    sections = [
        RenderedSection(heading="Tiến độ mốc", lines=("Hoàn thành: 3",)),
        RenderedSection(heading="Rủi ro", lines=("Đang mở: 1",)),
    ]

    # Act
    payload = render_report_docx("Báo cáo tuần", sections)

    # Assert
    texts = _paragraph_texts(payload)
    assert "Báo cáo tuần" in texts
    assert "Tiến độ mốc" in texts
    assert "Rủi ro" in texts
    assert "Hoàn thành: 3" in texts


def test_rendered_docx_is_a_valid_zip_package() -> None:
    # Act
    payload = render_report_docx("Báo cáo", [])

    # Assert: .docx là gói ZIP (chữ ký PK)
    assert payload[:2] == b"PK"


def test_pm_weekly_template_lists_sections_in_declared_order() -> None:
    # Act
    template = get_template(ReportKind.PM_WEEKLY)

    # Assert
    titles = [section.title for section in template.sections]
    assert titles[0] == "Thông tin dự án"
    assert "Rủi ro và vướng mắc" in titles


@pytest.mark.parametrize("kind", list(ReportKind))
def test_every_report_kind_has_a_template(kind: ReportKind) -> None:
    # Act
    template = get_template(kind)

    # Assert
    assert template.sections
    assert template.kind == kind

import pytest

from app.core.drive_file_kinds import DriveFileKind
from app.core.drive_preview_rules import (
    PREVIEW_MAX_BYTES,
    DrivePreviewNotAllowedError,
    DrivePreviewTooLargeError,
    check_preview_size,
    preview_media_type,
)

pytestmark = pytest.mark.unit


def test_pdf_and_image_are_previewable_with_their_mime_type() -> None:
    # Arrange / Act
    pdf_type = preview_media_type(DriveFileKind.PDF)
    image_type = preview_media_type(DriveFileKind.IMAGE)

    # Assert
    assert pdf_type == "application/pdf"
    assert image_type == "image/jpeg"


@pytest.mark.parametrize("kind", [DriveFileKind.DOCX, DriveFileKind.XLSX, DriveFileKind.AUDIO])
def test_office_and_audio_files_are_not_previewable(kind: DriveFileKind) -> None:
    # Arrange / Act / Assert
    with pytest.raises(DrivePreviewNotAllowedError):
        preview_media_type(kind)


def test_unsupported_file_without_kind_is_not_previewable() -> None:
    # Arrange / Act / Assert
    with pytest.raises(DrivePreviewNotAllowedError):
        preview_media_type(None)


def test_file_at_size_limit_is_allowed() -> None:
    # Arrange / Act / Assert: không ném lỗi là đạt
    check_preview_size(PREVIEW_MAX_BYTES)


def test_file_over_size_limit_is_rejected() -> None:
    # Arrange / Act / Assert
    with pytest.raises(DrivePreviewTooLargeError):
        check_preview_size(PREVIEW_MAX_BYTES + 1)


def test_file_with_unknown_size_is_not_previewable() -> None:
    # Arrange / Act / Assert
    with pytest.raises(DrivePreviewNotAllowedError):
        check_preview_size(None)

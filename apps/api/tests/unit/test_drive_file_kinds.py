import pytest

from app.core.drive_file_kinds import DriveFileKind, classify_file

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("file_name", "expected"),
    [
        ("BCKTKT_v2.docx", DriveFileKind.DOCX),
        ("Quyet_dinh_phe_duyet.pdf", DriveFileKind.PDF),
        ("Bang_khoi_luong.xlsx", DriveFileKind.XLSX),
        ("anh_hien_truong.jpg", DriveFileKind.IMAGE),
        ("anh_hien_truong.JPEG", DriveFileKind.IMAGE),
        ("ghi_am_hop.m4a", DriveFileKind.AUDIO),
    ],
)
def test_supported_extension_is_classified(file_name: str, expected: DriveFileKind) -> None:
    # Arrange
    # Act
    kind = classify_file(file_name)

    # Assert
    assert kind is expected


def test_extension_match_ignores_letter_case() -> None:
    # Arrange
    file_name = "BAO_CAO_TUAN.DOCX"

    # Act
    kind = classify_file(file_name)

    # Assert
    assert kind is DriveFileKind.DOCX


@pytest.mark.parametrize("file_name", ["ghi_chu.txt", "archive.zip", "no_extension"])
def test_unsupported_file_is_skipped(file_name: str) -> None:
    # Arrange
    # Act
    kind = classify_file(file_name)

    # Assert
    assert kind is None

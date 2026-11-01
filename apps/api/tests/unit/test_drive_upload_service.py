import pytest

from app.integrations.drive_gateway import DriveEntry
from app.services.drive_upload import DriveFolderNotFoundError, upload_to_project_folder
from tests.fakes.fake_drive_writer import FakeDriveWriter

pytestmark = pytest.mark.unit

ROOT = "root-du-an"
REPORT_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
FOLDER_MIME = "application/vnd.google-apps.folder"


def _folder(folder_id: str, name: str, parent: str) -> DriveEntry:
    return DriveEntry(
        drive_file_id=folder_id,
        parent_id=parent,
        name=name,
        mime_type=FOLDER_MIME,
        size=None,
        web_view_link=None,
        modified_time="2026-10-01T00:00:00Z",
        is_folder=True,
    )


def _writer() -> FakeDriveWriter:
    return FakeDriveWriter(
        tree={
            ROOT: [_folder("f-bao-cao", "Báo cáo tuần", ROOT)],
            "f-bao-cao": [_folder("f-2026", "2026", "f-bao-cao")],
        }
    )


def test_pushing_same_file_twice_updates_instead_of_duplicating() -> None:
    # Arrange
    writer = _writer()
    path = ("Báo cáo tuần", "2026")

    # Act
    first = upload_to_project_folder(
        writer, ROOT, path, "bao_cao_tuan_01.docx", b"ban 1", REPORT_MIME
    )
    second = upload_to_project_folder(
        writer, ROOT, path, "bao_cao_tuan_01.docx", b"ban 2", REPORT_MIME
    )

    # Assert
    assert first.created is True
    assert second.created is False
    assert first.file_id == second.file_id
    assert len(writer.uploads) == 1
    assert writer.uploads[("f-2026", "bao_cao_tuan_01.docx")][1] == b"ban 2"


def test_file_lands_in_folder_resolved_by_path_from_root() -> None:
    # Arrange
    writer = _writer()

    # Act
    upload_to_project_folder(writer, ROOT, ("Báo cáo tuần", "2026"), "a.docx", b"x", REPORT_MIME)

    # Assert
    assert ("f-2026", "a.docx") in writer.uploads


def test_missing_folder_is_reported_and_nothing_is_created() -> None:
    # Arrange
    writer = _writer()

    # Act / Assert
    with pytest.raises(DriveFolderNotFoundError):
        upload_to_project_folder(writer, ROOT, ("Biên bản bàn giao",), "bb.docx", b"x", REPORT_MIME)
    assert writer.uploads == {}

import json
from typing import Any

import httplib2
import pytest
from googleapiclient.errors import HttpError

from app.integrations.drive import DriveResponseError, GoogleDriveWriter
from tests.fakes.fake_google_drive_service import FakeGoogleDriveService

pytestmark = pytest.mark.unit

FOLDER_ID = "folder-pmis"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _no_sleep(_seconds: float) -> None:
    return None


def _raw_file(file_id: str, name: str) -> dict[str, Any]:
    return {
        "id": file_id,
        "name": name,
        "mimeType": DOCX_MIME,
        "parents": [FOLDER_ID],
        "modifiedTime": "2026-11-01T00:00:00.000Z",
    }


def _rate_limit_error() -> HttpError:
    content = json.dumps({"error": {"errors": [{"reason": "userRateLimitExceeded"}]}}).encode()
    return HttpError(httplib2.Response({"status": 403}), content)


def test_upsert_creates_file_when_name_is_not_in_folder() -> None:
    # Arrange
    service = FakeGoogleDriveService([{"files": []}, {"id": "new-1"}])
    writer = GoogleDriveWriter(service, sleep=_no_sleep)

    # Act
    result = writer.upsert_file(FOLDER_ID, "bao_cao.docx", b"noi dung", DOCX_MIME)

    # Assert
    assert (result.file_id, result.created) == ("new-1", True)
    assert service.calls[1]["body"] == {"name": "bao_cao.docx", "parents": [FOLDER_ID]}


def test_upsert_updates_existing_file_instead_of_creating_a_duplicate() -> None:
    # Arrange
    service = FakeGoogleDriveService(
        [{"files": [_raw_file("old-1", "bao_cao.docx")]}, {"id": "old-1"}]
    )
    writer = GoogleDriveWriter(service, sleep=_no_sleep)

    # Act
    result = writer.upsert_file(FOLDER_ID, "bao_cao.docx", b"ban moi", DOCX_MIME)

    # Assert
    assert (result.file_id, result.created) == ("old-1", False)
    assert service.calls[1]["fileId"] == "old-1"


def test_find_child_escapes_quotes_in_the_query() -> None:
    # Arrange
    service = FakeGoogleDriveService([{"files": []}])
    writer = GoogleDriveWriter(service, sleep=_no_sleep)

    # Act
    writer.find_child(FOLDER_ID, "Bao cao 'tuan'.docx")

    # Assert
    assert "name = 'Bao cao \\'tuan\\'.docx'" in service.calls[0]["q"]


def test_invalid_folder_id_is_rejected_before_any_call() -> None:
    # Arrange
    service = FakeGoogleDriveService([])
    writer = GoogleDriveWriter(service, sleep=_no_sleep)

    # Act / Assert
    with pytest.raises(ValueError):
        writer.upsert_file("x' or name contains 'y", "a.docx", b"x", DOCX_MIME)
    assert service.calls == []


def test_rate_limited_upsert_is_retried() -> None:
    # Arrange
    service = FakeGoogleDriveService([_rate_limit_error(), {"files": []}, {"id": "new-2"}])
    writer = GoogleDriveWriter(service, sleep=_no_sleep)

    # Act
    result = writer.upsert_file(FOLDER_ID, "a.docx", b"x", DOCX_MIME)

    # Assert
    assert result.file_id == "new-2"
    assert len(service.calls) == 3


def test_listed_response_without_id_is_rejected() -> None:
    # Arrange
    service = FakeGoogleDriveService([{"files": [{"name": "thieu-id.docx"}]}])
    writer = GoogleDriveWriter(service, sleep=_no_sleep)

    # Act / Assert
    with pytest.raises(DriveResponseError):
        writer.find_child(FOLDER_ID, "thieu-id.docx")

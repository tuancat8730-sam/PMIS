import json
from typing import Any

import httplib2
import pytest
from googleapiclient.errors import HttpError

from app.integrations.drive import (
    DriveApiError,
    DriveResponseError,
    GoogleDriveGateway,
    to_drive_entry,
)
from tests.fakes.fake_google_drive_service import FakeGoogleDriveService

pytestmark = pytest.mark.unit

FOLDER_MIME = "application/vnd.google-apps.folder"


def _no_sleep(_seconds: float) -> None:
    return None


def _raw_file(**overrides: Any) -> dict[str, Any]:
    return {
        "id": "file-1",
        "name": "bien_ban.pdf",
        "mimeType": "application/pdf",
        "parents": ["folder-root"],
        "size": "2048",
        "webViewLink": "https://drive.example/file-1",
        "modifiedTime": "2026-10-05T08:00:00.000Z",
        **overrides,
    }


def _http_error(status: int, reason: str) -> HttpError:
    content = json.dumps({"error": {"errors": [{"reason": reason}], "code": status}}).encode()
    return HttpError(httplib2.Response({"status": status}), content)


def test_maps_google_payload_to_drive_entry() -> None:
    # Arrange
    raw = _raw_file()

    # Act
    entry = to_drive_entry(raw)

    # Assert
    assert entry.drive_file_id == "file-1"
    assert entry.parent_id == "folder-root"
    assert entry.size == 2048
    assert entry.is_folder is False


def test_folder_mime_type_marks_entry_as_folder() -> None:
    # Arrange
    raw = _raw_file(mimeType=FOLDER_MIME, size=None)

    # Act
    entry = to_drive_entry(raw)

    # Assert
    assert entry.is_folder is True
    assert entry.size is None


def test_payload_without_id_is_rejected() -> None:
    # Arrange
    raw = _raw_file()
    del raw["id"]

    # Act / Assert
    with pytest.raises(DriveResponseError):
        to_drive_entry(raw)


def test_list_children_follows_next_page_token() -> None:
    # Arrange
    service = FakeGoogleDriveService(
        [
            {"files": [_raw_file(id="a")], "nextPageToken": "page-2"},
            {"files": [_raw_file(id="b")]},
        ]
    )
    gateway = GoogleDriveGateway(service, sleep=_no_sleep)

    # Act
    entries = gateway.list_children("folder-root")

    # Assert
    assert [entry.drive_file_id for entry in entries] == ["a", "b"]
    assert service.calls[1]["pageToken"] == "page-2"


def test_list_children_query_excludes_trashed_items_of_given_folder() -> None:
    # Arrange
    service = FakeGoogleDriveService([{"files": []}])
    gateway = GoogleDriveGateway(service, sleep=_no_sleep)

    # Act
    gateway.list_children("folder-root")

    # Assert
    assert service.calls[0]["q"] == "'folder-root' in parents and trashed = false"


def test_folder_id_with_query_characters_is_rejected_before_any_call() -> None:
    # Arrange
    service = FakeGoogleDriveService([])
    gateway = GoogleDriveGateway(service, sleep=_no_sleep)

    # Act / Assert
    with pytest.raises(ValueError):
        gateway.list_children("x' or name contains 'y")
    assert service.calls == []


def test_rate_limited_request_is_retried_with_backoff_then_succeeds() -> None:
    # Arrange
    delays: list[float] = []
    service = FakeGoogleDriveService(
        [_http_error(403, "userRateLimitExceeded"), {"files": [_raw_file()]}]
    )
    gateway = GoogleDriveGateway(service, sleep=delays.append)

    # Act
    entries = gateway.list_children("folder-root")

    # Assert
    assert len(entries) == 1
    assert len(delays) == 1
    assert delays[0] > 0


def test_permission_error_is_not_retried() -> None:
    # Arrange
    delays: list[float] = []
    service = FakeGoogleDriveService([_http_error(403, "insufficientFilePermissions")])
    gateway = GoogleDriveGateway(service, sleep=delays.append)

    # Act / Assert
    with pytest.raises(DriveApiError) as excinfo:
        gateway.list_children("folder-root")
    assert excinfo.value.status == 403
    assert delays == []


def test_gives_up_after_max_retries_on_persistent_server_error() -> None:
    # Arrange
    service = FakeGoogleDriveService([_http_error(503, "backendError") for _ in range(10)])
    gateway = GoogleDriveGateway(service, sleep=_no_sleep, max_retries=2)

    # Act / Assert
    with pytest.raises(DriveApiError):
        gateway.list_children("folder-root")
    assert len(service.calls) == 3  # lần đầu + 2 lần thử lại

import json
from typing import Any

import httplib2
import pytest
from googleapiclient.errors import HttpError

from app.integrations.drive import GoogleDriveGateway
from tests.fakes.fake_google_drive_service import FakeGoogleDriveService

pytestmark = pytest.mark.unit

PDF_BYTES = b"%PDF-1.4 noi dung thu"


def _no_sleep(_seconds: float) -> None:
    return None


def _http_error(status: int, reason: str) -> HttpError:
    content = json.dumps({"error": {"errors": [{"reason": reason}], "code": status}}).encode()
    return HttpError(httplib2.Response({"status": status}), content)


def test_download_returns_media_bytes_for_the_requested_file() -> None:
    # Arrange
    service = FakeGoogleDriveService([PDF_BYTES])
    gateway = GoogleDriveGateway(service, sleep=_no_sleep)

    # Act
    content = gateway.download("file-1")

    # Assert
    assert content == PDF_BYTES
    assert service.calls[-1]["fileId"] == "file-1"


def test_download_retries_rate_limited_request_then_succeeds() -> None:
    # Arrange
    service = FakeGoogleDriveService([_http_error(429, "rateLimitExceeded"), PDF_BYTES])
    gateway = GoogleDriveGateway(service, sleep=_no_sleep)

    # Act
    content: Any = gateway.download("file-1")

    # Assert
    assert content == PDF_BYTES
    assert len(service.calls) == 2


def test_download_rejects_malformed_file_id_before_any_call() -> None:
    # Arrange
    service = FakeGoogleDriveService([])
    gateway = GoogleDriveGateway(service, sleep=_no_sleep)

    # Act / Assert
    with pytest.raises(ValueError):
        gateway.download("../khong-hop-le")
    assert service.calls == []

"""Adapter Google Drive: đọc (chiều Drive → App) và ghi (chiều App → Drive), dùng tài khoản dịch vụ.

Đường dẫn file khóa được nạp từ cấu hình (biến môi trường), không bao giờ ghi vào mã hay log.
Lỗi giới hạn tốc độ và lỗi máy chủ tạm thời được thử lại có backoff, có giới hạn số lần.
"""

import io
import json
import logging
import re
import time
from collections.abc import Callable, Mapping
from functools import partial
from typing import Any

from google.oauth2 import service_account
from google.oauth2.credentials import Credentials as UserCredentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload

from app.integrations.drive_gateway import DriveEntry, UpsertResult

logger = logging.getLogger(__name__)

DRIVE_READONLY_SCOPE = "https://www.googleapis.com/auth/drive.readonly"
DRIVE_WRITE_SCOPE = "https://www.googleapis.com/auth/drive"
DRIVE_API_NAME = "drive"
DRIVE_API_VERSION = "v3"
FOLDER_MIME = "application/vnd.google-apps.folder"
LIST_PAGE_SIZE = 1000
LIST_FIELDS = "nextPageToken, files(id, name, mimeType, parents, size, webViewLink, modifiedTime)"
FOLDER_ID_PATTERN = re.compile(r"[A-Za-z0-9_-]{1,128}")
RATE_LIMIT_REASONS = frozenset({"rateLimitExceeded", "userRateLimitExceeded"})
RATE_LIMIT_STATUS = 429
PERMISSION_DENIED_STATUS = 403
RETRYABLE_SERVER_STATUSES = frozenset({500, 502, 503, 504})
DEFAULT_MAX_RETRIES = 3
BACKOFF_BASE_SECONDS = 1.0


class DriveResponseError(ValueError):
    """Phản hồi của Drive không đúng cấu trúc mong đợi."""


class DriveApiError(RuntimeError):
    """Drive trả lỗi và không thể thử lại (quyền, không tìm thấy, hoặc đã hết số lần thử)."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status


def to_drive_entry(raw: Mapping[str, Any]) -> DriveEntry:
    mime_type = _required_str(raw, "mimeType")
    parents = raw.get("parents") or []
    return DriveEntry(
        drive_file_id=_required_str(raw, "id"),
        parent_id=parents[0] if parents else None,
        name=_required_str(raw, "name"),
        mime_type=mime_type,
        size=_optional_int(raw.get("size")),
        web_view_link=raw.get("webViewLink"),
        modified_time=_required_str(raw, "modifiedTime"),
        is_folder=mime_type == FOLDER_MIME,
    )


def _required_str(raw: Mapping[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise DriveResponseError(f"Phản hồi Drive thiếu trường {key}")
    return value


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise DriveResponseError("Kích thước file trong phản hồi Drive không hợp lệ") from exc


def _check_folder_id(folder_id: str) -> None:
    # ID được đưa vào câu truy vấn Drive, nên chỉ cho phép ký tự an toàn.
    if not FOLDER_ID_PATTERN.fullmatch(folder_id):
        raise ValueError("Mã thư mục Drive không hợp lệ")


def _escape_query_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def _error_reason(error: HttpError) -> str | None:
    try:
        payload = json.loads(error.content)
        return str(payload["error"]["errors"][0]["reason"])
    except (ValueError, KeyError, IndexError, TypeError):
        return None


def _is_retryable(status: int, reason: str | None) -> bool:
    if status == RATE_LIMIT_STATUS:
        return True
    if status == PERMISSION_DENIED_STATUS and reason in RATE_LIMIT_REASONS:
        return True
    return status in RETRYABLE_SERVER_STATUSES


def _run_with_retry(
    call: Callable[[], dict[str, Any]],
    sleep: Callable[[float], None],
    max_retries: int,
) -> dict[str, Any]:
    attempt = 0
    while True:
        try:
            return call()
        except HttpError as error:
            status = int(error.resp.status)
            reason = _error_reason(error)
            if not _is_retryable(status, reason) or attempt >= max_retries:
                raise DriveApiError(status, f"Drive trả lỗi {status} khi gọi API") from error
            delay = BACKOFF_BASE_SECONDS * (2**attempt)
            logger.warning(
                "Drive tạm từ chối (status=%s, reason=%s), thử lại sau %.1fs",
                status,
                reason,
                delay,
            )
            sleep(delay)
            attempt += 1


def _list_files_page(service: Any, query: str, page_token: str | None) -> dict[str, Any]:
    response: dict[str, Any] = (
        service.files()
        .list(
            q=query,
            fields=LIST_FIELDS,
            pageSize=LIST_PAGE_SIZE,
            pageToken=page_token,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        )
        .execute()
    )
    return response


def _build_service(key_file_path: str, scope: str) -> Any:
    credentials = service_account.Credentials.from_service_account_file(
        key_file_path, scopes=[scope]
    )
    return build(DRIVE_API_NAME, DRIVE_API_VERSION, credentials=credentials, cache_discovery=False)


class GoogleDriveGateway:
    """Cài đặt `DriveGateway` (chỉ đọc) bằng Google Drive API v3."""

    def __init__(
        self,
        service: Any,
        sleep: Callable[[float], None] = time.sleep,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        self._service = service
        self._sleep = sleep
        self._max_retries = max_retries

    @classmethod
    def from_service_account_file(cls, key_file_path: str) -> "GoogleDriveGateway":
        return cls(_build_service(key_file_path, DRIVE_READONLY_SCOPE))

    def list_children(self, folder_id: str) -> list[DriveEntry]:
        _check_folder_id(folder_id)
        query = f"'{folder_id}' in parents and trashed = false"
        entries: list[DriveEntry] = []
        page_token: str | None = None
        while True:
            page = _run_with_retry(
                partial(_list_files_page, self._service, query, page_token),
                self._sleep,
                self._max_retries,
            )
            entries.extend(to_drive_entry(raw) for raw in page.get("files", []))
            page_token = page.get("nextPageToken")
            if page_token is None:
                return entries


class GoogleDriveWriter:
    """Cài đặt `DriveWriter` (đọc và ghi) bằng Google Drive API v3. Chỉ dùng cho luồng đẩy file."""

    def __init__(
        self,
        service: Any,
        sleep: Callable[[float], None] = time.sleep,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        self._service = service
        self._sleep = sleep
        self._max_retries = max_retries

    @classmethod
    def from_oauth_token_file(cls, token_file_path: str) -> "GoogleDriveWriter":
        """Ghi bằng token OAuth của người dùng. Tài khoản dịch vụ không có quota trong My Drive."""
        credentials = UserCredentials.from_authorized_user_file(
            token_file_path, [DRIVE_WRITE_SCOPE]
        )
        return cls(
            build(DRIVE_API_NAME, DRIVE_API_VERSION, credentials=credentials, cache_discovery=False)
        )

    def find_child(self, folder_id: str, name: str) -> DriveEntry | None:
        _check_folder_id(folder_id)
        query = (
            f"'{folder_id}' in parents and name = '{_escape_query_value(name)}' and trashed = false"
        )
        page = _run_with_retry(
            partial(_list_files_page, self._service, query, None),
            self._sleep,
            self._max_retries,
        )
        files = page.get("files", [])
        return to_drive_entry(files[0]) if files else None

    def upsert_file(
        self, folder_id: str, name: str, content: bytes, mime_type: str
    ) -> UpsertResult:
        existing = self.find_child(folder_id, name)
        if existing is None:
            response = _run_with_retry(
                partial(self._create_file, folder_id, name, content, mime_type),
                self._sleep,
                self._max_retries,
            )
            return UpsertResult(file_id=_required_str(response, "id"), created=True)
        _run_with_retry(
            partial(self._update_file, existing.drive_file_id, content, mime_type),
            self._sleep,
            self._max_retries,
        )
        return UpsertResult(file_id=existing.drive_file_id, created=False)

    def _create_file(
        self, folder_id: str, name: str, content: bytes, mime_type: str
    ) -> dict[str, Any]:
        # Media được tạo mới ở mỗi lần thử, vì lần lỗi trước có thể đã đọc hết buffer.
        media = MediaIoBaseUpload(io.BytesIO(content), mimetype=mime_type, resumable=False)
        response: dict[str, Any] = (
            self._service.files()
            .create(body={"name": name, "parents": [folder_id]}, media_body=media, fields="id")
            .execute()
        )
        return response

    def _update_file(self, file_id: str, content: bytes, mime_type: str) -> dict[str, Any]:
        media = MediaIoBaseUpload(io.BytesIO(content), mimetype=mime_type, resumable=False)
        response: dict[str, Any] = (
            self._service.files().update(fileId=file_id, media_body=media, fields="id").execute()
        )
        return response

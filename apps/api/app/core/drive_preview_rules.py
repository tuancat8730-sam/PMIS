"""Quy tắc xem trực tiếp file Drive trong trình duyệt (thuần, không chạm mạng hay DB).

Chỉ PDF và ảnh được xem trực tiếp. Các loại khác phải tải về. Nội dung được đọc hết vào bộ nhớ
nên giới hạn kích thước là bắt buộc để bảo vệ server.
"""

from typing import Final

from app.core.drive_file_kinds import KIND_MIME_TYPES, DriveFileKind

PREVIEW_MAX_BYTES: Final = 25 * 1024 * 1024
PREVIEWABLE_KINDS: Final = frozenset({DriveFileKind.PDF, DriveFileKind.IMAGE})


class DrivePreviewError(Exception):
    """Lỗi chung khi xem trực tiếp file Drive."""


class DrivePreviewNotAllowedError(DrivePreviewError):
    """Loại file không xem trực tiếp được, hoặc không xác định được kích thước."""


class DrivePreviewTooLargeError(DrivePreviewError):
    """File vượt giới hạn kích thước xem trực tiếp."""


def preview_media_type(kind: DriveFileKind | None) -> str:
    """Trả về MIME type để trình duyệt hiển thị inline, hoặc ném lỗi nếu loại không xem được."""
    if kind is None or kind not in PREVIEWABLE_KINDS:
        raise DrivePreviewNotAllowedError("Loại file này không xem trực tiếp được")
    return KIND_MIME_TYPES[kind]


def download_media_type(kind: DriveFileKind | None) -> str:
    """Trả về MIME type khi tải về. Mọi loại đồng bộ được đều tải được, chỉ cần biết loại."""
    if kind is None:
        raise DrivePreviewNotAllowedError("Không xác định được loại file")
    return KIND_MIME_TYPES[kind]


def check_preview_size(file_size: int | None) -> None:
    """Kiểm tra kích thước trước khi tải.

    Không biết kích thước thì từ chối, để không bỏ qua giới hạn.
    """
    if file_size is None:
        raise DrivePreviewNotAllowedError("Không xác định được kích thước file")
    if file_size > PREVIEW_MAX_BYTES:
        raise DrivePreviewTooLargeError("File vượt quá giới hạn xem trực tiếp")

"""Cổng (Protocol) truy cập Google Drive. Nghiệp vụ chỉ phụ thuộc vào cổng này, không phụ thuộc SDK.

Adapter thật nằm ở `app/integrations/drive.py`; test dùng bản giả trong `tests/fakes/`.
"""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class DriveEntry:
    """Một mục (file hoặc thư mục) trả về từ Drive, đã chuẩn hóa thành kiểu nội bộ."""

    drive_file_id: str
    parent_id: str | None
    name: str
    mime_type: str
    size: int | None
    web_view_link: str | None
    modified_time: str
    is_folder: bool


class DriveGateway(Protocol):
    def list_children(self, folder_id: str) -> list[DriveEntry]:
        """Liệt kê con trực tiếp của một thư mục. Ném lỗi có kiểu khi Drive trả lỗi."""
        ...


@dataclass(frozen=True)
class UpsertResult:
    file_id: str
    created: bool


class DriveWriter(Protocol):
    """Cổng ghi (App → Drive). Tách khỏi `DriveGateway` để chỉ nơi cần ghi mới có quyền ghi."""

    def find_child(self, folder_id: str, name: str) -> DriveEntry | None:
        """Tìm một mục con theo tên trong thư mục, hoặc None nếu không có."""
        ...

    def upsert_file(
        self, folder_id: str, name: str, content: bytes, mime_type: str
    ) -> UpsertResult:
        """Tạo file theo tên, hoặc cập nhật nội dung nếu đã có file cùng tên trong thư mục."""
        ...

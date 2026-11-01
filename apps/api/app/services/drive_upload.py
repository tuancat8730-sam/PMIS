"""Đẩy file từ app lên thư mục của dự án trên Drive (chiều App → Drive).

Thư mục đích được duyệt theo đường dẫn tên từ thư mục gốc của dự án. Nếu thiếu thư mục thì báo lỗi,
không tự tạo thư mục trong Drive của khách hàng. Đẩy lại cùng tên file sẽ cập nhật, không tạo trùng.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from app.integrations.drive_gateway import DriveWriter


class DriveFolderNotFoundError(Exception):
    """Không tìm thấy một thư mục trong đường dẫn đích."""


@dataclass(frozen=True)
class UploadResult:
    file_id: str
    created: bool


def upload_to_project_folder(
    writer: DriveWriter,
    root_folder_id: str,
    folder_path: Sequence[str],
    file_name: str,
    content: bytes,
    mime_type: str,
) -> UploadResult:
    folder_id = _resolve_folder(writer, root_folder_id, folder_path)
    result = writer.upsert_file(folder_id, file_name, content, mime_type)
    return UploadResult(file_id=result.file_id, created=result.created)


def _resolve_folder(writer: DriveWriter, root_folder_id: str, folder_path: Sequence[str]) -> str:
    current_id = root_folder_id
    for segment in folder_path:
        entry = writer.find_child(current_id, segment)
        if entry is None or not entry.is_folder:
            raise DriveFolderNotFoundError(segment)
        current_id = entry.drive_file_id
    return current_id

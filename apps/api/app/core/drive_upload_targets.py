"""Ánh xạ loại file đẩy lên Drive → thư mục lưu trữ `(pmis)` trong thư mục gốc của dự án (thuần).

Chỉ lưu tên thư mục, không lưu ID. ID được tìm theo tên trong thư mục gốc của từng dự án,
nên cùng một ánh xạ dùng được cho mọi dự án. Các thư mục này do PMIS tạo, không dùng thư mục có sẵn.
"""

from collections.abc import Mapping
from enum import StrEnum
from types import MappingProxyType


class UploadKind(StrEnum):
    WEEKLY_REPORT = "WEEKLY_REPORT"
    HANDOVER_MINUTES = "HANDOVER_MINUTES"
    CONTRACT = "CONTRACT"
    FIELD_PHOTO = "FIELD_PHOTO"


UPLOAD_FOLDER_NAMES: Mapping[UploadKind, str] = MappingProxyType(
    {
        UploadKind.WEEKLY_REPORT: "Báo cáo tuần (pmis)",
        UploadKind.HANDOVER_MINUTES: "Biên bản bàn giao (pmis)",
        UploadKind.CONTRACT: "Hợp đồng (pmis)",
        UploadKind.FIELD_PHOTO: "Ảnh hiện trường (pmis)",
    }
)


def target_folder_path(kind: UploadKind) -> tuple[str, ...]:
    """Đường dẫn thư mục đích tính từ thư mục gốc của dự án."""
    return (UPLOAD_FOLDER_NAMES[kind],)

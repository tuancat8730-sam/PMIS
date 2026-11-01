"""Phân loại định dạng file trên Google Drive (thuần, không chạm mạng).

Chỉ các định dạng trong spec Phân hệ 3 mục 3 được đồng bộ. File khác bị bỏ qua.
"""

from enum import StrEnum
from types import MappingProxyType
from typing import Final


class DriveFileKind(StrEnum):
    DOCX = "DOCX"
    PDF = "PDF"
    XLSX = "XLSX"
    IMAGE = "IMAGE"
    AUDIO = "AUDIO"


_EXTENSION_KINDS: Final = MappingProxyType(
    {
        ".docx": DriveFileKind.DOCX,
        ".pdf": DriveFileKind.PDF,
        ".xlsx": DriveFileKind.XLSX,
        ".jpg": DriveFileKind.IMAGE,
        ".jpeg": DriveFileKind.IMAGE,
        ".m4a": DriveFileKind.AUDIO,
    }
)


DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

KIND_MIME_TYPES: Final = MappingProxyType(
    {
        DriveFileKind.DOCX: DOCX_MIME,
        DriveFileKind.PDF: "application/pdf",
        DriveFileKind.XLSX: XLSX_MIME,
        DriveFileKind.IMAGE: "image/jpeg",
        DriveFileKind.AUDIO: "audio/mp4",
    }
)


def classify_file(file_name: str) -> DriveFileKind | None:
    """Trả về loại file theo đuôi (không phân biệt hoa thường), hoặc None nếu không hỗ trợ."""
    dot_index = file_name.rfind(".")
    if dot_index == -1:
        return None
    return _EXTENSION_KINDS.get(file_name[dot_index:].lower())

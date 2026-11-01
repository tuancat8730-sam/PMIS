import asyncio
import hashlib
import io
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError

from app.core.exif_gps import GPS_SOURCE_BROWSER, GpsPoint, extract_gps
from app.core.field_rules import MIME_JPEG, MIME_PNG, detect_image_mime

PHOTO_EXTENSIONS: dict[str, str] = {MIME_JPEG: ".jpg", MIME_PNG: ".png"}
PHOTO_REJECTED_DETAIL = "Tệp không phải ảnh JPEG hoặc PNG hợp lệ"


class PhotoRejectedError(Exception):
    """Nội dung tệp không phải ảnh hợp lệ (sai chữ ký hoặc ảnh bị hỏng)."""


@dataclass(frozen=True)
class PhotoInspection:
    mime: str
    gps: GpsPoint | None


def _verify_decodable(content: bytes) -> None:
    try:
        with Image.open(io.BytesIO(content)) as image:
            image.verify()
    except (UnidentifiedImageError, OSError, SyntaxError) as exc:
        raise PhotoRejectedError from exc


def inspect_photo(content: bytes) -> PhotoInspection:
    """Kiểm tra ảnh theo nội dung, đọc GPS từ EXIF. Gọi trong thread riêng vì Pillow đồng bộ."""
    mime = detect_image_mime(content)
    if mime is None:
        raise PhotoRejectedError
    _verify_decodable(content)
    return PhotoInspection(mime=mime, gps=extract_gps(content))


def choose_gps(
    exif_gps: GpsPoint | None,
    browser_latitude: float | None,
    browser_longitude: float | None,
) -> GpsPoint | None:
    """EXIF là nguồn chính (Q4). Chỉ dùng vị trí trình duyệt khi ảnh không có EXIF GPS."""
    if exif_gps is not None:
        return exif_gps
    if browser_latitude is None or browser_longitude is None:
        return None
    return GpsPoint(
        latitude=browser_latitude,
        longitude=browser_longitude,
        source=GPS_SOURCE_BROWSER,
    )


def _storage_key(project_id: uuid.UUID, uploaded_at: datetime, mime: str) -> str:
    """Tên tệp do máy chủ sinh, không dùng tên người gửi, nên không có path traversal."""
    return f"{project_id}/{uploaded_at:%Y%m%d}/{uuid.uuid4().hex}{PHOTO_EXTENSIONS[mime]}"


def _write_file(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


async def store_photo_file(
    root: Path,
    *,
    project_id: uuid.UUID,
    content: bytes,
    mime: str,
    uploaded_at: datetime,
) -> str:
    """Lưu cục bộ trước (Q3), trả về khóa lưu trữ tương đối so với thư mục gốc."""
    key = _storage_key(project_id, uploaded_at, mime)
    await asyncio.to_thread(_write_file, root / key, content)
    return key


def build_photo_record(
    *,
    photo_id: uuid.UUID,
    kind: str,
    content: bytes,
    mime: str,
    storage_key: str,
    gps: GpsPoint | None,
    device_id: str,
    uploaded_at: datetime,
) -> dict[str, Any]:
    """Bản ghi ảnh lưu trong `delivery_handovers.site_photos` (JSONB)."""
    return {
        "id": str(photo_id),
        "kind": kind,
        "mime": mime,
        "size_bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "storage_key": storage_key,
        "gps": None
        if gps is None
        else {"latitude": gps.latitude, "longitude": gps.longitude, "source": gps.source},
        "device_id": device_id,
        "uploaded_at": uploaded_at.isoformat(),
    }

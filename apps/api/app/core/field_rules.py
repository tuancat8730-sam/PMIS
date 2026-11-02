import hashlib
import re

# 10 MB: đủ cho ảnh chụp điện thoại đã nén, chặn file quá lớn làm đầy ổ.
MAX_PHOTO_BYTES = 10 * 1024 * 1024
MIME_JPEG = "image/jpeg"
MIME_PNG = "image/png"

_JPEG_SIGNATURE = b"\xff\xd8\xff"
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_SIGNATURES: tuple[tuple[bytes, str], ...] = (
    (_JPEG_SIGNATURE, MIME_JPEG),
    (_PNG_SIGNATURE, MIME_PNG),
)

DEVICE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{8,64}$")


def detect_image_mime(content: bytes) -> str | None:
    """Nhận diện ảnh theo chữ ký nhị phân, không tin đuôi file. Trả None nếu không hỗ trợ."""
    for signature, mime in _SIGNATURES:
        if content.startswith(signature):
            return mime
    return None


def is_within_photo_size(size_bytes: int) -> bool:
    return size_bytes <= MAX_PHOTO_BYTES


def is_valid_device_id(value: str) -> bool:
    return DEVICE_ID_PATTERN.fullmatch(value) is not None


def hash_request_body(body: bytes) -> str:
    """Băm nội dung yêu cầu để phát hiện cùng Idempotency-Key nhưng khác dữ liệu."""
    return hashlib.sha256(body).hexdigest()

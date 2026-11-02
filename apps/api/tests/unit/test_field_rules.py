import pytest

from app.core.field_rules import (
    MAX_PHOTO_BYTES,
    detect_image_mime,
    hash_request_body,
    is_valid_device_id,
    is_within_photo_size,
)

JPEG_HEADER = b"\xff\xd8\xff\xe0" + b"\x00" * 16
PNG_HEADER = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16


@pytest.mark.unit
def test_detect_image_mime_accepts_jpeg_by_content() -> None:
    # Arrange
    content = JPEG_HEADER

    # Act
    mime = detect_image_mime(content)

    # Assert
    assert mime == "image/jpeg"


@pytest.mark.unit
def test_detect_image_mime_accepts_png_by_content() -> None:
    # Arrange
    content = PNG_HEADER

    # Act
    mime = detect_image_mime(content)

    # Assert
    assert mime == "image/png"


@pytest.mark.unit
@pytest.mark.parametrize(
    "content",
    [b"%PDF-1.7 ...", b"GIF89a....", b"<html></html>", b""],
    ids=["pdf", "gif", "html", "empty"],
)
def test_detect_image_mime_rejects_non_image_content(content: bytes) -> None:
    # Arrange / Act
    mime = detect_image_mime(content)

    # Assert
    assert mime is None


@pytest.mark.unit
def test_detect_image_mime_rejects_text_renamed_to_jpg() -> None:
    # Arrange: nội dung là văn bản, không có chữ ký ảnh dù đuôi file là .jpg
    content = "đây không phải ảnh".encode()

    # Act
    mime = detect_image_mime(content)

    # Assert
    assert mime is None


@pytest.mark.unit
def test_photo_size_limit_accepts_exact_limit_and_rejects_one_byte_more() -> None:
    # Arrange / Act / Assert
    assert is_within_photo_size(MAX_PHOTO_BYTES) is True
    assert is_within_photo_size(MAX_PHOTO_BYTES + 1) is False


@pytest.mark.unit
@pytest.mark.parametrize("value", ["tablet-01", "A1_b2.c3-d4", "device_000000001"])
def test_valid_device_id_is_accepted(value: str) -> None:
    # Arrange / Act / Assert
    assert is_valid_device_id(value) is True


@pytest.mark.unit
@pytest.mark.parametrize("value", ["", "short", "có dấu tiếng Việt", "a" * 65, "bad id with space"])
def test_invalid_device_id_is_rejected(value: str) -> None:
    # Arrange / Act / Assert
    assert is_valid_device_id(value) is False


@pytest.mark.unit
def test_hash_request_body_is_stable_and_differs_for_different_bodies() -> None:
    # Arrange
    body_a = b'{"delivery_status":"INSTALLED"}'
    body_b = b'{"delivery_status":"ISSUE_REPORTED"}'

    # Act
    first = hash_request_body(body_a)
    again = hash_request_body(body_a)
    other = hash_request_body(body_b)

    # Assert
    assert first == again
    assert first != other
    assert len(first) == 64

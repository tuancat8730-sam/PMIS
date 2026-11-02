import io

import pytest
from PIL import Image

from app.core.exif_gps import GPS_SOURCE_EXIF, GpsPoint, extract_gps

GPS_IFD_TAG = 0x8825


def _jpeg_bytes(exif: Image.Exif | None = None) -> bytes:
    buffer = io.BytesIO()
    image = Image.new("RGB", (4, 4), color=(120, 80, 40))
    if exif is None:
        image.save(buffer, format="JPEG")
    else:
        image.save(buffer, format="JPEG", exif=exif.tobytes())
    return buffer.getvalue()


def _exif_with_gps(
    lat: tuple[float, float, float],
    lat_ref: str,
    lon: tuple[float, float, float],
    lon_ref: str,
) -> Image.Exif:
    exif = Image.Exif()
    exif[GPS_IFD_TAG] = {1: lat_ref, 2: lat, 3: lon_ref, 4: lon}
    return exif


@pytest.mark.unit
def test_extract_gps_reads_north_east_coordinates_from_exif() -> None:
    # Arrange: 10°46'30" B, 106°41'0" Đ (TP.HCM)
    content = _jpeg_bytes(
        _exif_with_gps((10.0, 46.0, 30.0), "N", (106.0, 41.0, 0.0), "E"),
    )

    # Act
    point = extract_gps(content)

    # Assert
    assert point is not None
    assert point.latitude == pytest.approx(10.775, abs=1e-4)
    assert point.longitude == pytest.approx(106.6833, abs=1e-4)
    assert point.source == GPS_SOURCE_EXIF


@pytest.mark.unit
def test_extract_gps_negates_southern_and_western_hemispheres() -> None:
    # Arrange
    content = _jpeg_bytes(
        _exif_with_gps((33.0, 52.0, 0.0), "S", (151.0, 12.0, 0.0), "W"),
    )

    # Act
    point = extract_gps(content)

    # Assert
    assert point is not None
    assert point.latitude == pytest.approx(-33.8667, abs=1e-4)
    assert point.longitude == pytest.approx(-151.2, abs=1e-4)


@pytest.mark.unit
def test_extract_gps_returns_none_when_image_has_no_exif() -> None:
    # Arrange
    content = _jpeg_bytes()

    # Act
    point = extract_gps(content)

    # Assert
    assert point is None


@pytest.mark.unit
def test_extract_gps_returns_none_when_exif_has_no_gps_block() -> None:
    # Arrange: EXIF có dữ liệu khác nhưng không có khối GPS
    exif = Image.Exif()
    exif[0x010F] = "Camera Co"
    content = _jpeg_bytes(exif)

    # Act
    point = extract_gps(content)

    # Assert
    assert point is None


@pytest.mark.unit
def test_gps_point_is_immutable() -> None:
    # Arrange
    point = GpsPoint(latitude=10.0, longitude=106.0, source=GPS_SOURCE_EXIF)

    # Act / Assert
    with pytest.raises(AttributeError):
        point.latitude = 0.0  # type: ignore[misc]

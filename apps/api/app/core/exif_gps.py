import io
from dataclasses import dataclass

from PIL import Image, UnidentifiedImageError

GPS_SOURCE_EXIF = "EXIF"
GPS_SOURCE_BROWSER = "BROWSER"
GPS_IFD_TAG = 0x8825
_GPS_LATITUDE_TAG = 2
_GPS_LATITUDE_REF_TAG = 1
_GPS_LONGITUDE_TAG = 4
_GPS_LONGITUDE_REF_TAG = 3
_NEGATIVE_REFS = frozenset({"S", "W"})
_DMS_PARTS = 3


@dataclass(frozen=True)
class GpsPoint:
    latitude: float
    longitude: float
    source: str


def _dms_to_decimal(dms: tuple[float, ...], ref: str) -> float:
    degrees, minutes, seconds = (float(part) for part in dms[:_DMS_PARTS])
    value = degrees + minutes / 60 + seconds / 3600
    return -value if ref.strip().upper() in _NEGATIVE_REFS else value


def extract_gps(content: bytes) -> GpsPoint | None:
    """Đọc tọa độ GPS từ khối EXIF. Trả None nếu ảnh không có GPS hoặc không đọc được."""
    try:
        with Image.open(io.BytesIO(content)) as image:
            gps = image.getexif().get_ifd(GPS_IFD_TAG)
    except (UnidentifiedImageError, OSError, SyntaxError):
        return None
    if not gps or _GPS_LATITUDE_TAG not in gps or _GPS_LONGITUDE_TAG not in gps:
        return None
    latitude = _dms_to_decimal(gps[_GPS_LATITUDE_TAG], str(gps.get(_GPS_LATITUDE_REF_TAG, "N")))
    longitude = _dms_to_decimal(gps[_GPS_LONGITUDE_TAG], str(gps.get(_GPS_LONGITUDE_REF_TAG, "E")))
    return GpsPoint(latitude=latitude, longitude=longitude, source=GPS_SOURCE_EXIF)

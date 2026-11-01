import io
import uuid
from typing import Any

import httpx
import pytest
from PIL import Image
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import Role
from app.models.delivery_handover import DeliveryHandover
from app.models.equipment import EquipmentCatalog
from app.models.equipment_serial import EquipmentSerial
from tests.integration.helpers import UserFactory, create_project, login_as

pytestmark = pytest.mark.integration

DEVICE_A = "tablet-field-001"
DEVICE_B = "tablet-field-002"
GPS_TAG = 0x8825
MAX_PHOTO_BYTES_PLUS_ONE = 10 * 1024 * 1024 + 1


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _field_headers(token: str, device_id: str, key: str | None = None) -> dict[str, str]:
    return {
        **_bearer(token),
        "X-Device-Id": device_id,
        "Idempotency-Key": key or str(uuid.uuid4()),
    }


def _jpeg_with_gps() -> bytes:
    exif = Image.Exif()
    exif[GPS_TAG] = {1: "N", 2: (10.0, 46.0, 30.0), 3: "E", 4: (106.0, 41.0, 0.0)}
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), color=(10, 200, 30)).save(buffer, format="JPEG", exif=exif.tobytes())
    return buffer.getvalue()


def _jpeg_without_gps() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), color=(10, 200, 30)).save(buffer, format="JPEG")
    return buffer.getvalue()


async def _setup_project_with_handover(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> tuple[str, str, str]:
    """Trả về (token PM, project_id, handover_id) của một dòng giao hàng đầu tiên."""
    await make_user(email="pm-field@example.com", role=Role.PM)
    token = await login_as(client, "pm-field@example.com")
    project_id = await create_project(client, token)
    unit = await client.post(
        f"/api/v1/projects/{project_id}/beneficiary-units",
        json={
            "unit_code": "LD-01",
            "official_name": "Trường LD-01",
            "former_name": None,
            "unit_type": "THPT",
            "cluster_code": "LD-1",
            "cluster_name": "LD-1",
        },
        headers=_bearer(token),
    )
    assert unit.status_code == 201, unit.text
    generated = await client.post(
        f"/api/v1/projects/{project_id}/delivery-handovers/generate",
        headers=_bearer(token),
    )
    assert generated.status_code == 201, generated.text
    listing = await client.get(
        f"/api/v1/projects/{project_id}/delivery-handovers",
        headers=_bearer(token),
    )
    handover_id = listing.json()[0]["id"]
    return token, project_id, handover_id


async def _status_patch(
    client: httpx.AsyncClient,
    token: str,
    project_id: str,
    handover_id: str,
    *,
    device_id: str,
    key: str,
    status: str,
    expected_version: int,
) -> httpx.Response:
    return await client.patch(
        f"/api/v1/projects/{project_id}/field/delivery-handovers/{handover_id}/status",
        json={"delivery_status": status, "expected_version": expected_version},
        headers=_field_headers(token, device_id, key),
    )


async def _seed_serial(session: AsyncSession, project_id: str, handover_id: str) -> str:
    """Chèn một mã hàng và một serial trực tiếp vào DB (E9 chưa có API nhập serial)."""
    project_uuid = uuid.UUID(project_id)
    catalog = EquipmentCatalog(
        project_id=project_uuid,
        item_code="MH-01",
        item_name="Máy chiếu thử nghiệm",
        category_batch="DOT_1",
        contract_quantity=1,
        technical_specs={},
    )
    session.add(catalog)
    await session.flush()
    serial = EquipmentSerial(
        project_id=project_uuid,
        equipment_id=catalog.id,
        handover_id=uuid.UUID(handover_id),
        serial_number_primary="SN-E10-0001",
    )
    session.add(serial)
    await session.commit()
    return str(serial.id)


async def _handover_row(session: AsyncSession, handover_id: str) -> DeliveryHandover:
    result = await session.execute(
        select(DeliveryHandover).where(DeliveryHandover.id == uuid.UUID(handover_id))
    )
    row = result.scalar_one()
    await session.refresh(row)
    return row


@pytest.mark.parametrize("header_name", ["Idempotency-Key", "X-Device-Id"])
async def test_field_write_without_required_header_returns_422(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    header_name: str,
) -> None:
    # Arrange
    token, project_id, handover_id = await _setup_project_with_handover(client, make_user)
    headers = _field_headers(token, DEVICE_A)
    del headers[header_name]

    # Act
    response = await client.patch(
        f"/api/v1/projects/{project_id}/field/delivery-handovers/{handover_id}/status",
        json={"delivery_status": "IN_TRANSIT", "expected_version": 1},
        headers=headers,
    )

    # Assert
    assert response.status_code == 422


async def test_invalid_device_id_returns_422(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id, handover_id = await _setup_project_with_handover(client, make_user)

    # Act
    response = await _status_patch(
        client,
        token,
        project_id,
        handover_id,
        device_id="bad id!",
        key=str(uuid.uuid4()),
        status="IN_TRANSIT",
        expected_version=1,
    )

    # Assert
    assert response.status_code == 422


async def test_replayed_status_update_returns_stored_response_and_does_not_bump_twice(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    session: AsyncSession,
) -> None:
    # Arrange
    token, project_id, handover_id = await _setup_project_with_handover(client, make_user)
    key = str(uuid.uuid4())
    first = await _status_patch(
        client,
        token,
        project_id,
        handover_id,
        device_id=DEVICE_A,
        key=key,
        status="IN_TRANSIT",
        expected_version=1,
    )

    # Act: thiết bị không nhận được phản hồi và gửi lại cùng khóa, cùng nội dung
    replay = await _status_patch(
        client,
        token,
        project_id,
        handover_id,
        device_id=DEVICE_A,
        key=key,
        status="IN_TRANSIT",
        expected_version=1,
    )

    # Assert
    assert first.status_code == 200
    assert replay.status_code == 200
    assert replay.json() == first.json()
    row = await _handover_row(session, handover_id)
    assert row.version == 2
    assert row.delivery_status == "IN_TRANSIT"


async def test_same_key_with_different_body_returns_422(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id, handover_id = await _setup_project_with_handover(client, make_user)
    key = str(uuid.uuid4())
    await _status_patch(
        client,
        token,
        project_id,
        handover_id,
        device_id=DEVICE_A,
        key=key,
        status="IN_TRANSIT",
        expected_version=1,
    )

    # Act
    response = await _status_patch(
        client,
        token,
        project_id,
        handover_id,
        device_id=DEVICE_A,
        key=key,
        status="ISSUE_REPORTED",
        expected_version=1,
    )

    # Assert
    assert response.status_code == 422


async def test_same_key_from_another_device_is_not_replayed(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange: khóa chỉ có nghĩa trong phạm vi một thiết bị
    token, project_id, handover_id = await _setup_project_with_handover(client, make_user)
    key = str(uuid.uuid4())
    await _status_patch(
        client,
        token,
        project_id,
        handover_id,
        device_id=DEVICE_A,
        key=key,
        status="IN_TRANSIT",
        expected_version=1,
    )

    # Act
    response = await _status_patch(
        client,
        token,
        project_id,
        handover_id,
        device_id=DEVICE_B,
        key=key,
        status="IN_TRANSIT",
        expected_version=1,
    )

    # Assert: thiết bị B dùng phiên bản cũ nên nhận 409, không được dùng kết quả của thiết bị A
    assert response.status_code == 409


async def test_stale_version_returns_409_with_current_state_and_keeps_data(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    session: AsyncSession,
) -> None:
    # Arrange: thiết bị A cập nhật trước, thiết bị B còn giữ phiên bản 1
    token, project_id, handover_id = await _setup_project_with_handover(client, make_user)
    await _status_patch(
        client,
        token,
        project_id,
        handover_id,
        device_id=DEVICE_A,
        key=str(uuid.uuid4()),
        status="IN_TRANSIT",
        expected_version=1,
    )

    # Act
    response = await _status_patch(
        client,
        token,
        project_id,
        handover_id,
        device_id=DEVICE_B,
        key=str(uuid.uuid4()),
        status="ISSUE_REPORTED",
        expected_version=1,
    )

    # Assert
    assert response.status_code == 409
    body: dict[str, Any] = response.json()
    assert body["current"] == {"delivery_status": "IN_TRANSIT", "version": 2}
    row = await _handover_row(session, handover_id)
    assert row.delivery_status == "IN_TRANSIT"
    assert row.version == 2


async def test_stale_serial_verification_returns_409(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    session: AsyncSession,
) -> None:
    # Arrange
    token, project_id, handover_id = await _setup_project_with_handover(client, make_user)
    serial_id = await _seed_serial(session, project_id, handover_id)
    url = f"/api/v1/projects/{project_id}/field/serials/{serial_id}/verification"
    first = await client.patch(
        url,
        json={"verification_status": "ĐẠT", "expected_version": 1},
        headers=_field_headers(token, DEVICE_A),
    )

    # Act
    second = await client.patch(
        url,
        json={"verification_status": "KHÔNG ĐẠT", "expected_version": 1},
        headers=_field_headers(token, DEVICE_B),
    )

    # Assert
    assert first.status_code == 200
    assert first.json()["verification_status"] == "ĐẠT"
    assert second.status_code == 409
    assert second.json()["current"] == {"verification_status": "ĐẠT", "version": 2}


async def test_photo_with_fake_image_extension_is_rejected(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange: văn bản được đổi đuôi thành .jpg
    token, project_id, handover_id = await _setup_project_with_handover(client, make_user)

    # Act
    response = await client.post(
        f"/api/v1/projects/{project_id}/field/delivery-handovers/{handover_id}/photos",
        data={"kind": "SITE"},
        files={"file": ("anh.jpg", "không phải ảnh".encode(), "image/jpeg")},
        headers=_field_headers(token, DEVICE_A),
    )

    # Assert
    assert response.status_code == 422


async def test_photo_over_size_limit_is_rejected_with_413(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id, handover_id = await _setup_project_with_handover(client, make_user)
    oversized = b"\xff\xd8\xff" + b"\x00" * (MAX_PHOTO_BYTES_PLUS_ONE - 3)

    # Act
    response = await client.post(
        f"/api/v1/projects/{project_id}/field/delivery-handovers/{handover_id}/photos",
        data={"kind": "SITE"},
        files={"file": ("lon.jpg", oversized, "image/jpeg")},
        headers=_field_headers(token, DEVICE_A),
    )

    # Assert
    assert response.status_code == 413


async def test_photo_with_exif_gps_is_stored_with_exif_source(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    session: AsyncSession,
) -> None:
    # Arrange
    token, project_id, handover_id = await _setup_project_with_handover(client, make_user)

    # Act
    response = await client.post(
        f"/api/v1/projects/{project_id}/field/delivery-handovers/{handover_id}/photos",
        data={"kind": "SITE"},
        files={"file": ("anh.jpg", _jpeg_with_gps(), "image/jpeg")},
        headers=_field_headers(token, DEVICE_A),
    )

    # Assert
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["mime"] == "image/jpeg"
    assert body["gps"]["source"] == "EXIF"
    assert body["gps"]["latitude"] == pytest.approx(10.775, abs=1e-4)
    row = await _handover_row(session, handover_id)
    assert len(row.site_photos) == 1
    assert row.site_photos[0]["id"] == body["id"]


async def test_photo_without_exif_uses_browser_gps_when_provided(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id, handover_id = await _setup_project_with_handover(client, make_user)

    # Act
    response = await client.post(
        f"/api/v1/projects/{project_id}/field/delivery-handovers/{handover_id}/photos",
        data={"kind": "SITE", "latitude": "10.7769", "longitude": "106.7009"},
        files={"file": ("anh.jpg", _jpeg_without_gps(), "image/jpeg")},
        headers=_field_headers(token, DEVICE_A),
    )

    # Assert
    assert response.status_code == 201, response.text
    assert response.json()["gps"]["source"] == "BROWSER"


async def test_photo_without_any_gps_returns_null_gps(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id, handover_id = await _setup_project_with_handover(client, make_user)

    # Act
    response = await client.post(
        f"/api/v1/projects/{project_id}/field/delivery-handovers/{handover_id}/photos",
        data={"kind": "SIGNED_HANDOVER"},
        files={"file": ("bien-ban.jpg", _jpeg_without_gps(), "image/jpeg")},
        headers=_field_headers(token, DEVICE_A),
    )

    # Assert
    assert response.status_code == 201, response.text
    assert response.json()["gps"] is None
    assert response.json()["kind"] == "SIGNED_HANDOVER"


async def test_replayed_photo_upload_does_not_duplicate_the_photo(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    session: AsyncSession,
) -> None:
    # Arrange
    token, project_id, handover_id = await _setup_project_with_handover(client, make_user)
    key = str(uuid.uuid4())
    url = f"/api/v1/projects/{project_id}/field/delivery-handovers/{handover_id}/photos"
    content = _jpeg_without_gps()

    # Act
    first = await client.post(
        url,
        data={"kind": "SITE"},
        files={"file": ("anh.jpg", content, "image/jpeg")},
        headers=_field_headers(token, DEVICE_A, key),
    )
    replay = await client.post(
        url,
        data={"kind": "SITE"},
        files={"file": ("anh.jpg", content, "image/jpeg")},
        headers=_field_headers(token, DEVICE_A, key),
    )

    # Assert
    assert first.status_code == 201
    assert replay.json() == first.json()
    row = await _handover_row(session, handover_id)
    assert len(row.site_photos) == 1


async def test_handover_listing_exposes_version_for_field_devices(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id, _handover_id = await _setup_project_with_handover(client, make_user)

    # Act
    response = await client.get(
        f"/api/v1/projects/{project_id}/delivery-handovers",
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 200
    assert response.json()[0]["version"] == 1


async def test_contractor_without_project_membership_cannot_update_status(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id, handover_id = await _setup_project_with_handover(client, make_user)
    await make_user(email="contractor-field@example.com", role=Role.CONTRACTOR)
    outsider = await login_as(client, "contractor-field@example.com")

    # Act
    response = await _status_patch(
        client,
        outsider,
        project_id,
        handover_id,
        device_id=DEVICE_A,
        key=str(uuid.uuid4()),
        status="IN_TRANSIT",
        expected_version=1,
    )

    # Assert
    assert response.status_code == 403

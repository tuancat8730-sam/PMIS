from typing import Any

import httpx
import pytest

from app.core.rbac import Role
from app.core.sample_criteria_catalog import SAMPLE_CRITERIA
from tests.integration.helpers import UserFactory, create_project, login_as

pytestmark = pytest.mark.integration

CATALOG_PAYLOAD: dict[str, Any] = {
    "item_stt": 206,
    "item_code": "A3520",
    "item_name": "Bộ máy tính để bàn Tin học",
    "category_batch": "DOT_1",
    "brand": "FPT Elead",
    "origin_country": "Việt Nam",
    "manufacture_year": 2026,
    "contract_quantity": 1420,
    "unit_price": "12500000.00",
    "technical_specs": {"TC07": "Intel i5"},
}


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _criteria(failed_code: str | None = None) -> list[dict[str, str]]:
    return [
        {"code": criterion.code, "result": "KHÔNG ĐẠT" if criterion.code == failed_code else "ĐẠT"}
        for criterion in SAMPLE_CRITERIA
    ]


def _inspection_payload(criteria: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "inspected_on": "2026-11-02",
        "inspector": "TVGS Nguyễn Văn A",
        "serial_number_sample": "SN-SAMPLE-001",
        "criteria": criteria,
    }


async def _pm_with_project(client: httpx.AsyncClient, make_user: UserFactory) -> tuple[str, str]:
    await make_user(email="pm@example.com", role=Role.PM)
    token = await login_as(client, "pm@example.com")
    project_id = await create_project(client, token)
    return token, project_id


async def _create_item(client: httpx.AsyncClient, token: str, project_id: str) -> str:
    response = await client.post(
        f"/api/v1/projects/{project_id}/equipment/catalog",
        json=CATALOG_PAYLOAD,
        headers=_bearer(token),
    )
    assert response.status_code == 201
    return str(response.json()["id"])


async def test_pm_creates_catalog_item(client: httpx.AsyncClient, make_user: UserFactory) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)

    # Act
    response = await client.post(
        f"/api/v1/projects/{project_id}/equipment/catalog",
        json=CATALOG_PAYLOAD,
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 201
    assert response.json()["sample_approval_status"] == "PENDING"


async def test_duplicate_catalog_item_in_same_batch_returns_conflict(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    await _create_item(client, token, project_id)

    # Act
    response = await client.post(
        f"/api/v1/projects/{project_id}/equipment/catalog",
        json=CATALOG_PAYLOAD,
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 409


async def test_passing_sample_marks_item_approved(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    item_id = await _create_item(client, token, project_id)

    # Act
    response = await client.post(
        f"/api/v1/projects/{project_id}/equipment/catalog/{item_id}/sample-inspections",
        json=_inspection_payload(_criteria()),
        headers=_bearer(token),
    )
    catalog = await client.get(
        f"/api/v1/projects/{project_id}/equipment/catalog",
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 201
    assert response.json()["conclusion"] == "ĐẠT"
    assert catalog.json()[0]["sample_approval_status"] == "APPROVED"


async def test_failing_criterion_requires_sample_rework(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    item_id = await _create_item(client, token, project_id)

    # Act
    response = await client.post(
        f"/api/v1/projects/{project_id}/equipment/catalog/{item_id}/sample-inspections",
        json=_inspection_payload(_criteria(failed_code="TC05")),
        headers=_bearer(token),
    )
    catalog = await client.get(
        f"/api/v1/projects/{project_id}/equipment/catalog",
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 201
    assert response.json()["conclusion"] == "YÊU CẦU LÀM LẠI MẪU"
    assert catalog.json()[0]["sample_approval_status"] == "REWORK_REQUIRED"


async def test_sample_with_missing_criteria_is_rejected(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    item_id = await _create_item(client, token, project_id)

    # Act
    response = await client.post(
        f"/api/v1/projects/{project_id}/equipment/catalog/{item_id}/sample-inspections",
        json=_inspection_payload(_criteria()[:-1]),
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 422


async def test_user_outside_project_cannot_create_catalog_item(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    _token, project_id = await _pm_with_project(client, make_user)
    await make_user(email="outsider@example.com", role=Role.FIELD_ENGINEER)
    outsider_token = await login_as(client, "outsider@example.com")

    # Act
    response = await client.post(
        f"/api/v1/projects/{project_id}/equipment/catalog",
        json=CATALOG_PAYLOAD,
        headers=_bearer(outsider_token),
    )

    # Assert
    assert response.status_code == 403

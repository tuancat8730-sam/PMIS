import httpx
import pytest

from app.core.rbac import Role
from tests.integration.helpers import (
    UserFactory,
    create_project,
    login_as,
)

pytestmark = pytest.mark.integration

EVIDENCE_REF = "Biên bản nghiệm thu H3 số 12/BB-2026"


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _pm_with_project(client: httpx.AsyncClient, make_user: UserFactory) -> tuple[str, str]:
    await make_user(email="pm@example.com", role=Role.PM)
    token = await login_as(client, "pm@example.com")
    project_id = await create_project(client, token)
    return token, project_id


async def _add_member_with_role(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    pm_token: str,
    project_id: str,
    email: str,
    role: Role,
) -> str:
    user = await make_user(email=email, role=role)
    await client.post(
        f"/api/v1/projects/{project_id}/members",
        json={"user_id": str(user.id), "role": role.value},
        headers=_bearer(pm_token),
    )
    return await login_as(client, email)


async def _create_hold_point(client: httpx.AsyncClient, token: str, project_id: str) -> str:
    response = await client.post(
        f"/api/v1/projects/{project_id}/hold-points",
        json={"code": "H3", "name": "Điểm dừng H3"},
        headers=_bearer(token),
    )
    assert response.status_code == 201, response.text
    hold_point_id: str = response.json()["id"]
    return hold_point_id


async def test_hold_point_is_cleared_only_after_all_three_parties_confirm(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    pm_token, project_id = await _pm_with_project(client, make_user)
    hold_point_id = await _create_hold_point(client, pm_token, project_id)
    supervisor_token = await _add_member_with_role(
        client, make_user, pm_token, project_id, "tvgs@example.com", Role.SUPERVISION_CONSULTANT
    )
    contractor_token = await _add_member_with_role(
        client, make_user, pm_token, project_id, "contractor@example.com", Role.CONTRACTOR
    )
    confirm_url = f"/api/v1/projects/{project_id}/hold-points/{hold_point_id}/confirmations"

    # Act
    await client.post(
        confirm_url,
        json={"party": "CDT", "evidence_ref": EVIDENCE_REF},
        headers=_bearer(pm_token),
    )
    await client.post(
        confirm_url,
        json={"party": "TVGS", "evidence_ref": EVIDENCE_REF},
        headers=_bearer(supervisor_token),
    )
    partial = await client.get(
        f"/api/v1/projects/{project_id}/hold-points", headers=_bearer(pm_token)
    )
    await client.post(
        confirm_url,
        json={"party": "NHA_THAU", "evidence_ref": EVIDENCE_REF},
        headers=_bearer(contractor_token),
    )
    complete = await client.get(
        f"/api/v1/projects/{project_id}/hold-points", headers=_bearer(pm_token)
    )

    # Assert
    assert partial.json()[0]["cleared"] is False
    assert partial.json()[0]["missing_parties"] == ["NHA_THAU"]
    assert complete.json()[0]["cleared"] is True
    assert complete.json()[0]["missing_parties"] == []


async def test_party_confirming_with_wrong_project_role_is_forbidden(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    pm_token, project_id = await _pm_with_project(client, make_user)
    hold_point_id = await _create_hold_point(client, pm_token, project_id)
    contractor_token = await _add_member_with_role(
        client, make_user, pm_token, project_id, "contractor@example.com", Role.CONTRACTOR
    )

    # Act
    response = await client.post(
        f"/api/v1/projects/{project_id}/hold-points/{hold_point_id}/confirmations",
        json={"party": "CDT", "evidence_ref": EVIDENCE_REF},
        headers=_bearer(contractor_token),
    )

    # Assert
    assert response.status_code == 403


async def test_same_party_confirming_twice_returns_409(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    pm_token, project_id = await _pm_with_project(client, make_user)
    hold_point_id = await _create_hold_point(client, pm_token, project_id)
    confirm_url = f"/api/v1/projects/{project_id}/hold-points/{hold_point_id}/confirmations"
    await client.post(
        confirm_url,
        json={"party": "CDT", "evidence_ref": EVIDENCE_REF},
        headers=_bearer(pm_token),
    )

    # Act
    response = await client.post(
        confirm_url,
        json={"party": "CDT", "evidence_ref": EVIDENCE_REF},
        headers=_bearer(pm_token),
    )

    # Assert
    assert response.status_code == 409


async def test_confirmation_requires_evidence_reference(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    pm_token, project_id = await _pm_with_project(client, make_user)
    hold_point_id = await _create_hold_point(client, pm_token, project_id)

    # Act
    response = await client.post(
        f"/api/v1/projects/{project_id}/hold-points/{hold_point_id}/confirmations",
        json={"party": "CDT", "evidence_ref": ""},
        headers=_bearer(pm_token),
    )

    # Assert
    assert response.status_code == 422

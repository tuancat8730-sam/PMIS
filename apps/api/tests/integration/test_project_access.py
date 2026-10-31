import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import Role
from app.models.audit_log import AuditLog
from app.models.user import User
from tests.integration.helpers import (
    CONTRACT_PAYLOAD,
    UserFactory,
    create_contract,
    create_project,
    login_as,
)

pytestmark = pytest.mark.integration

PERSONNEL_PAYLOAD = {
    "full_name": "Nguyễn Quang Hân",
    "position_role": "Chủ nhiệm",
    "national_id_cccd": "001085012345",
}
STAKEHOLDER_PAYLOAD = {"role": "INVESTOR", "organization_name": "Sở GD&ĐT TP.HCM"}


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _login(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    email: str,
    role: Role,
) -> tuple[User, str]:
    user = await make_user(email=email, role=role)
    return user, await login_as(client, email)


async def _add_member(
    client: httpx.AsyncClient,
    pm_token: str,
    project_id: str,
    user: User,
    role: Role,
) -> httpx.Response:
    return await client.post(
        f"/api/v1/projects/{project_id}/members",
        json={"user_id": str(user.id), "role": role.value},
        headers=_bearer(pm_token),
    )


async def test_creator_becomes_project_pm_and_can_view_it(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    _, pm_token = await _login(client, make_user, "pm@example.com", Role.PM)
    project_id = await create_project(client, pm_token)

    # Act
    response = await client.get(f"/api/v1/projects/{project_id}", headers=_bearer(pm_token))

    # Assert
    assert response.status_code == 200


async def test_pm_who_is_not_a_member_cannot_view_project(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    _, owner_token = await _login(client, make_user, "owner@example.com", Role.PM)
    project_id = await create_project(client, owner_token)
    _, other_token = await _login(client, make_user, "other@example.com", Role.PM)

    # Act
    response = await client.get(f"/api/v1/projects/{project_id}", headers=_bearer(other_token))

    # Assert
    assert response.status_code == 403


async def test_list_shows_only_projects_the_user_belongs_to(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    _, first_token = await _login(client, make_user, "first@example.com", Role.PM)
    _, second_token = await _login(client, make_user, "second@example.com", Role.PM)
    await create_project(client, first_token)
    await create_project(client, second_token, code="SGD-LD-TB10-2026")

    # Act
    first_list = await client.get("/api/v1/projects", headers=_bearer(first_token))
    second_list = await client.get("/api/v1/projects", headers=_bearer(second_token))

    # Assert
    assert [item["code"] for item in first_list.json()] == ["SGD-HCM-CSVC-2026"]
    assert [item["code"] for item in second_list.json()] == ["SGD-LD-TB10-2026"]


async def test_admin_lists_all_projects_and_views_any_project(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    _, pm_token = await _login(client, make_user, "pm@example.com", Role.PM)
    project_id = await create_project(client, pm_token)
    _, admin_token = await _login(client, make_user, "admin@example.com", Role.ADMIN)

    # Act
    listing = await client.get("/api/v1/projects", headers=_bearer(admin_token))
    detail = await client.get(f"/api/v1/projects/{project_id}", headers=_bearer(admin_token))

    # Assert
    assert [item["code"] for item in listing.json()] == ["SGD-HCM-CSVC-2026"]
    assert detail.status_code == 200


async def test_pm_adds_member_and_member_can_view_project(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    _, pm_token = await _login(client, make_user, "pm@example.com", Role.PM)
    project_id = await create_project(client, pm_token)
    contractor, contractor_token = await _login(
        client, make_user, "contractor@example.com", Role.CONTRACTOR
    )
    await _add_member(client, pm_token, project_id, contractor, Role.CONTRACTOR)

    # Act
    response = await client.get(f"/api/v1/projects/{project_id}", headers=_bearer(contractor_token))

    # Assert
    assert response.status_code == 200


async def test_member_can_list_project_members(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    pm_user, pm_token = await _login(client, make_user, "pm@example.com", Role.PM)
    project_id = await create_project(client, pm_token)
    consultant, _ = await _login(client, make_user, "consultant@example.com", Role.PM_CONSULTANT)
    await _add_member(client, pm_token, project_id, consultant, Role.PM_CONSULTANT)

    # Act
    response = await client.get(f"/api/v1/projects/{project_id}/members", headers=_bearer(pm_token))

    # Assert
    assert response.status_code == 200
    assert sorted(item["role"] for item in response.json()) == ["PM", "PM_CONSULTANT"]
    assert str(pm_user.id) in [item["user_id"] for item in response.json()]


async def test_only_project_pm_can_add_members(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    _, pm_token = await _login(client, make_user, "pm@example.com", Role.PM)
    project_id = await create_project(client, pm_token)
    investor, investor_token = await _login(
        client, make_user, "investor@example.com", Role.INVESTOR
    )
    await _add_member(client, pm_token, project_id, investor, Role.INVESTOR)
    candidate, _ = await _login(client, make_user, "candidate@example.com", Role.CONTRACTOR)

    # Act
    response = await _add_member(client, investor_token, project_id, candidate, Role.CONTRACTOR)

    # Assert
    assert response.status_code == 403


async def test_adding_same_member_twice_returns_409(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    _, pm_token = await _login(client, make_user, "pm@example.com", Role.PM)
    project_id = await create_project(client, pm_token)
    contractor, _ = await _login(client, make_user, "contractor@example.com", Role.CONTRACTOR)
    await _add_member(client, pm_token, project_id, contractor, Role.CONTRACTOR)

    # Act
    response = await _add_member(client, pm_token, project_id, contractor, Role.CONTRACTOR)

    # Assert
    assert response.status_code == 409


async def test_adding_unknown_user_returns_404(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    _, pm_token = await _login(client, make_user, "pm@example.com", Role.PM)
    project_id = await create_project(client, pm_token)

    # Act
    response = await client.post(
        f"/api/v1/projects/{project_id}/members",
        json={"user_id": "00000000-0000-0000-0000-000000000000", "role": "CONTRACTOR"},
        headers=_bearer(pm_token),
    )

    # Assert
    assert response.status_code == 404


async def test_admin_cannot_be_a_project_member_role(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    _, pm_token = await _login(client, make_user, "pm@example.com", Role.PM)
    project_id = await create_project(client, pm_token)
    candidate, _ = await _login(client, make_user, "candidate@example.com", Role.CONTRACTOR)

    # Act
    response = await _add_member(client, pm_token, project_id, candidate, Role.ADMIN)

    # Assert
    assert response.status_code == 422


async def test_member_addition_is_audited_with_actor(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    session: AsyncSession,
) -> None:
    # Arrange
    pm_user, pm_token = await _login(client, make_user, "pm@example.com", Role.PM)
    project_id = await create_project(client, pm_token)
    contractor, _ = await _login(client, make_user, "contractor@example.com", Role.CONTRACTOR)

    # Act
    await _add_member(client, pm_token, project_id, contractor, Role.CONTRACTOR)

    # Assert
    audited = (
        await session.execute(select(AuditLog).where(AuditLog.action == "project_member.add"))
    ).scalar_one()
    assert audited.actor_id == pm_user.id
    assert audited.changes == {"user_id": str(contractor.id), "role": "CONTRACTOR"}


async def test_contractor_member_cannot_add_stakeholder(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    _, pm_token = await _login(client, make_user, "pm@example.com", Role.PM)
    project_id = await create_project(client, pm_token)
    contractor, contractor_token = await _login(
        client, make_user, "contractor@example.com", Role.CONTRACTOR
    )
    await _add_member(client, pm_token, project_id, contractor, Role.CONTRACTOR)

    # Act
    response = await client.post(
        f"/api/v1/projects/{project_id}/stakeholders",
        json=STAKEHOLDER_PAYLOAD,
        headers=_bearer(contractor_token),
    )

    # Assert
    assert response.status_code == 403


async def test_pm_consultant_member_reads_contracts_but_cannot_write(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    _, pm_token = await _login(client, make_user, "pm@example.com", Role.PM)
    project_id = await create_project(client, pm_token)
    await create_contract(client, pm_token, project_id)
    consultant, consultant_token = await _login(
        client, make_user, "consultant@example.com", Role.PM_CONSULTANT
    )
    await _add_member(client, pm_token, project_id, consultant, Role.PM_CONSULTANT)
    url = f"/api/v1/projects/{project_id}/contracts"

    # Act
    read = await client.get(url, headers=_bearer(consultant_token))
    write = await client.post(url, json=CONTRACT_PAYLOAD, headers=_bearer(consultant_token))

    # Assert
    assert read.status_code == 200
    assert write.status_code == 403


async def test_pm_who_is_not_member_cannot_access_personnel(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    _, owner_token = await _login(client, make_user, "owner@example.com", Role.PM)
    project_id = await create_project(client, owner_token)
    contract_id = await create_contract(client, owner_token, project_id)
    _, other_token = await _login(client, make_user, "other@example.com", Role.PM)

    # Act
    read = await client.get(
        f"/api/v1/contracts/{contract_id}/personnel", headers=_bearer(other_token)
    )
    write = await client.post(
        f"/api/v1/contracts/{contract_id}/personnel",
        json=PERSONNEL_PAYLOAD,
        headers=_bearer(other_token),
    )

    # Assert
    assert read.status_code == 403
    assert write.status_code == 403


async def test_project_pm_reads_and_writes_personnel(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    _, pm_token = await _login(client, make_user, "pm@example.com", Role.PM)
    project_id = await create_project(client, pm_token)
    contract_id = await create_contract(client, pm_token, project_id)

    # Act
    write = await client.post(
        f"/api/v1/contracts/{contract_id}/personnel",
        json=PERSONNEL_PAYLOAD,
        headers=_bearer(pm_token),
    )
    read = await client.get(f"/api/v1/contracts/{contract_id}/personnel", headers=_bearer(pm_token))

    # Assert
    assert write.status_code == 201
    assert read.status_code == 200


async def test_pm_consultant_member_cannot_read_personnel(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    _, pm_token = await _login(client, make_user, "pm@example.com", Role.PM)
    project_id = await create_project(client, pm_token)
    contract_id = await create_contract(client, pm_token, project_id)
    consultant, consultant_token = await _login(
        client, make_user, "consultant@example.com", Role.PM_CONSULTANT
    )
    await _add_member(client, pm_token, project_id, consultant, Role.PM_CONSULTANT)

    # Act
    response = await client.get(
        f"/api/v1/contracts/{contract_id}/personnel", headers=_bearer(consultant_token)
    )

    # Assert
    assert response.status_code == 403


async def test_admin_writes_personnel_without_membership(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    _, pm_token = await _login(client, make_user, "pm@example.com", Role.PM)
    project_id = await create_project(client, pm_token)
    contract_id = await create_contract(client, pm_token, project_id)
    _, admin_token = await _login(client, make_user, "admin@example.com", Role.ADMIN)

    # Act
    response = await client.post(
        f"/api/v1/contracts/{contract_id}/personnel",
        json=PERSONNEL_PAYLOAD,
        headers=_bearer(admin_token),
    )

    # Assert
    assert response.status_code == 201

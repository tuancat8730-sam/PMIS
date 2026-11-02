from datetime import date
from decimal import Decimal
from uuid import UUID

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import Role
from app.models.contract import Contract
from tests.integration.helpers import UserFactory, create_project, login_as

pytestmark = pytest.mark.integration


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_contract_list_exposes_overview_fields(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    session: AsyncSession,
) -> None:
    # Arrange
    await make_user(email="pm-hop-dong-tong-quan@example.com", role=Role.PM)
    token = await login_as(client, "pm-hop-dong-tong-quan@example.com")
    project_id = await create_project(client, token)
    session.add(
        Contract(
            project_id=UUID(project_id),
            package_name="Gói TVGS",
            package_kind="CONSULTING",
            contract_number="24.8.26/HĐTV/SGDĐT-CRYSTAL",
            signed_date=date(2026, 8, 24),
            expiration_date=date(2027, 1, 21),
            contract_value=Decimal("120000000.00"),
            contractor_name="Công ty TNHH Đầu tư Thiết bị Crystal",
            role_label="Tư vấn giám sát",
            contact_person="Thái Thanh Hưng (GS trưởng), Thuy, Luận",
            status_note="Giám sát 8 bước, 10 điểm dừng HG-H9, H10",
        )
    )
    await session.commit()

    # Act
    response = await client.get(f"/api/v1/projects/{project_id}/contracts", headers=_bearer(token))

    # Assert
    assert response.status_code == 200
    [contract] = response.json()
    assert contract["contractor_name"] == "Công ty TNHH Đầu tư Thiết bị Crystal"
    assert contract["role_label"] == "Tư vấn giám sát"
    assert contract["contact_person"] == "Thái Thanh Hưng (GS trưởng), Thuy, Luận"
    assert contract["status_note"] == "Giám sát 8 bước, 10 điểm dừng HG-H9, H10"


async def test_contract_without_overview_fields_returns_null(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    session: AsyncSession,
) -> None:
    # Arrange
    await make_user(email="pm-hop-dong-trong@example.com", role=Role.PM)
    token = await login_as(client, "pm-hop-dong-trong@example.com")
    project_id = await create_project(client, token)
    session.add(
        Contract(
            project_id=UUID(project_id),
            package_name="Gói thầu chính",
            contract_value=Decimal("4848186000.00"),
        )
    )
    await session.commit()

    # Act
    response = await client.get(f"/api/v1/projects/{project_id}/contracts", headers=_bearer(token))

    # Assert
    [contract] = response.json()
    assert contract["contractor_name"] is None
    assert contract["role_label"] is None
    assert contract["contact_person"] is None
    assert contract["status_note"] is None

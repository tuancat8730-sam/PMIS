from uuid import UUID

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import Role
from app.models.project_technical_requirement import ProjectTechnicalRequirement
from tests.integration.helpers import UserFactory, create_project, login_as

pytestmark = pytest.mark.integration


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _requirements_url(project_id: str) -> str:
    return f"/api/v1/projects/{project_id}/technical-requirements"


async def test_pm_lists_requirements_in_sort_order_with_all_columns(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    session: AsyncSession,
) -> None:
    # Arrange
    await make_user(email="pm-ky-thuat@example.com", role=Role.PM)
    token = await login_as(client, "pm-ky-thuat@example.com")
    project_id = await create_project(client, token)
    session.add_all(
        [
            ProjectTechnicalRequirement(
                project_id=UUID(project_id),
                sort_order=2,
                item="Kiến trúc hệ thống",
                standard="Mô hình 3 lớp",
                legal_basis="QĐ 1595/QĐ-SGDĐT",
                solution="Frontend React/Angular, backend .NET Core",
                responsibility="LD DVN (DTH)",
                acceptance_criteria="Biên bản thử tải theo mốc",
                related_risk="Kiến trúc không đáp ứng tải",
                monitoring_status="Đang xây dựng",
            ),
            ProjectTechnicalRequirement(
                project_id=UUID(project_id),
                sort_order=1,
                item="Quy mô đối tượng",
                standard="Phục vụ Sở GD&ĐT, UBND phường/xã",
            ),
        ]
    )
    await session.commit()

    # Act
    response = await client.get(_requirements_url(project_id), headers=_bearer(token))

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert [row["item"] for row in body] == ["Quy mô đối tượng", "Kiến trúc hệ thống"]
    architecture = body[1]
    assert architecture["monitoring_status"] == "Đang xây dựng"
    assert architecture["responsibility"] == "LD DVN (DTH)"
    assert body[0]["solution"] is None

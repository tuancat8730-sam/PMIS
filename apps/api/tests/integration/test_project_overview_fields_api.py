import httpx
import pytest

from app.core.rbac import Role
from tests.integration.helpers import UserFactory, create_project, login_as

pytestmark = pytest.mark.integration

LEGAL_REPRESENTATIVE = "Ông Nguyễn Văn Hiếu — Giám đốc Sở GD&ĐT"
QLDA_FORM = "Chủ đầu tư thuê tư vấn quản lý dự án (Công ty Sài Gòn Mới)"
DISBURSEMENT_DEADLINE = "09/12/2026 (Hạn chót giải ngân niên độ tài chính năm 2026)"


async def test_project_detail_returns_overview_fields(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    await make_user(email="pm-tong-quan-truong@example.com", role=Role.PM)
    token = await login_as(client, "pm-tong-quan-truong@example.com")
    project_id = await create_project(
        client,
        token,
        legal_representative=LEGAL_REPRESENTATIVE,
        qlda_form=QLDA_FORM,
        disbursement_deadline=DISBURSEMENT_DEADLINE,
    )

    # Act
    response = await client.get(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body["legal_representative"] == LEGAL_REPRESENTATIVE
    assert body["qlda_form"] == QLDA_FORM
    assert body["disbursement_deadline"] == DISBURSEMENT_DEADLINE


async def test_project_without_overview_fields_returns_null(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    await make_user(email="pm-tong-quan-trong@example.com", role=Role.PM)
    token = await login_as(client, "pm-tong-quan-trong@example.com")
    project_id = await create_project(client, token)

    # Act
    response = await client.get(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Assert
    body = response.json()
    assert body["legal_representative"] is None
    assert body["qlda_form"] is None
    assert body["disbursement_deadline"] is None

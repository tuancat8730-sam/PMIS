from typing import Any
from uuid import UUID

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import Role
from app.models.drive_file import DriveFile
from app.models.legal_document import DocMaturityStatus, LegalDocument, LegalPhaseGroup
from tests.integration.helpers import UserFactory, create_project, login_as

pytestmark = pytest.mark.integration

PM_EMAIL = "pm-suggest@example.com"
ROOT = "root-goi-y"


async def _seed_file_and_document(session: AsyncSession, project_id: str) -> tuple[UUID, str]:
    project_uuid = UUID(project_id)
    drive_row = DriveFile(
        project_id=project_uuid,
        drive_file_id="file-qd",
        file_name="1595_QD_SGDDT_chu_truong.pdf",
        drive_path="1595_QD_SGDDT_chu_truong.pdf",
    )
    document = LegalDocument(
        project_id=project_uuid,
        phase_group=LegalPhaseGroup.PREPARATION,
        doc_code_symbol="1595/QĐ-SGDĐT",
        doc_name="Quyết định phê duyệt chủ trương đầu tư",
        maturity_status=DocMaturityStatus.MISSING,
    )
    session.add_all([drive_row, document])
    await session.commit()
    return document.id, drive_row.drive_file_id


async def test_suggestions_link_file_to_document_without_changing_maturity(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    session: AsyncSession,
) -> None:
    # Arrange
    await make_user(email=PM_EMAIL, role=Role.PM)
    token = await login_as(client, PM_EMAIL)
    project_id = await create_project(client, token, drive_root_folder_id=ROOT)
    document_id, drive_file_id = await _seed_file_and_document(session, project_id)

    # Act
    response = await client.get(
        f"/api/v1/projects/{project_id}/drive/suggestions",
        headers=_bearer(token),
    )
    documents = await client.get(
        f"/api/v1/projects/{project_id}/legal-documents",
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 200, response.text
    body: list[dict[str, Any]] = response.json()
    assert body == [
        {"drive_file_id": drive_file_id, "document_id": str(document_id), "reason": "symbol"}
    ]
    assert [doc["maturity_status"] for doc in documents.json()] == ["MISSING"]


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}

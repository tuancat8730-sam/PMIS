from typing import Any

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.rbac import Role
from app.models.audit_log import AuditLog
from tests.integration.helpers import (
    UserFactory,
    create_project,
    limited_client,
    login_as,
)

pytestmark = pytest.mark.integration

LEGAL_PAYLOAD: dict[str, Any] = {
    "stt": 1,
    "phase_group": "PREPARATION",
    "doc_code_symbol": "1595/QĐ-SGDĐT",
    "doc_name": "Quyết định phê duyệt chủ trương đầu tư",
    "issuing_authority": "Sở GD&ĐT TP.HCM",
    "issue_date": "2026-01-10",
    "assigned_to": "PM",
    "due_date": "2026-03-01",
}

CHAIN_TO_CLOSED = [
    "DRAFT_DOCX",
    "SUBMITTED_REVIEW",
    "WAITING_SIGNATURE",
    "SIGNED_SCAN_PDF",
    "VERIFIED_CLOSED",
]


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _docs_url(project_id: str) -> str:
    return f"/api/v1/projects/{project_id}/legal-documents"


async def _pm_with_project(client: httpx.AsyncClient, make_user: UserFactory) -> tuple[str, str]:
    await make_user(email="pm-phap-ly@example.com", role=Role.PM)
    token = await login_as(client, "pm-phap-ly@example.com")
    project_id = await create_project(client, token)
    return token, project_id


async def _create_doc(
    client: httpx.AsyncClient,
    token: str,
    project_id: str,
    **overrides: Any,
) -> dict[str, Any]:
    response = await client.post(
        _docs_url(project_id),
        json={**LEGAL_PAYLOAD, **overrides},
        headers=_bearer(token),
    )
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


async def _transition(
    client: httpx.AsyncClient,
    token: str,
    project_id: str,
    doc_id: str,
    body: dict[str, Any],
) -> httpx.Response:
    return await client.post(
        f"{_docs_url(project_id)}/{doc_id}/transitions",
        json=body,
        headers=_bearer(token),
    )


async def _advance_to(
    client: httpx.AsyncClient,
    token: str,
    project_id: str,
    doc_id: str,
    steps: list[str],
) -> None:
    """Đưa hồ sơ qua các bước tiến kế tiếp liên tiếp, mỗi bước kiểm tra trạng thái cũ."""
    current = "MISSING"
    for target in steps:
        response = await _transition(
            client,
            token,
            project_id,
            doc_id,
            {"expected_status": current, "target_status": target},
        )
        assert response.status_code == 200, response.text
        current = target


async def test_pm_creates_document_in_missing_status(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    session: AsyncSession,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)

    # Act
    response = await client.post(_docs_url(project_id), json=LEGAL_PAYLOAD, headers=_bearer(token))

    # Assert
    body = response.json()
    assert response.status_code == 201
    assert body["maturity_status"] == "MISSING"
    assert body["is_mandatory"] is True
    audited = (
        await session.execute(select(AuditLog).where(AuditLog.action == "legal_document.create"))
    ).scalar_one()
    assert audited.entity_id == body["id"]


async def test_duplicate_stt_in_same_project_returns_409(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    await _create_doc(client, token, project_id, stt=7)

    # Act
    response = await client.post(
        _docs_url(project_id), json={**LEGAL_PAYLOAD, "stt": 7}, headers=_bearer(token)
    )

    # Assert
    assert response.status_code == 409


async def test_unknown_phase_group_returns_422(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)

    # Act
    response = await client.post(
        _docs_url(project_id),
        json={**LEGAL_PAYLOAD, "phase_group": "GIAI_DOAN_LA"},
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 422


async def test_client_cannot_set_maturity_status_on_create(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)

    # Act
    response = await client.post(
        _docs_url(project_id),
        json={**LEGAL_PAYLOAD, "maturity_status": "VERIFIED_CLOSED"},
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 422


async def test_contractor_member_can_read_but_not_create(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    pm_token, project_id = await _pm_with_project(client, make_user)
    contractor = await make_user(email="nha-thau-phap-ly@example.com", role=Role.CONTRACTOR)
    await client.post(
        f"/api/v1/projects/{project_id}/members",
        json={"user_id": str(contractor.id), "role": Role.CONTRACTOR.value},
        headers=_bearer(pm_token),
    )
    contractor_token = await login_as(client, "nha-thau-phap-ly@example.com")

    # Act
    read = await client.get(_docs_url(project_id), headers=_bearer(contractor_token))
    write = await client.post(
        _docs_url(project_id), json=LEGAL_PAYLOAD, headers=_bearer(contractor_token)
    )

    # Assert
    assert read.status_code == 200
    assert write.status_code == 403


async def test_non_member_cannot_list_documents_returns_403(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    _, project_id = await _pm_with_project(client, make_user)
    await make_user(email="nguoi-ngoai-phap-ly@example.com", role=Role.PM)
    outsider_token = await login_as(client, "nguoi-ngoai-phap-ly@example.com")

    # Act
    response = await client.get(_docs_url(project_id), headers=_bearer(outsider_token))

    # Assert
    assert response.status_code == 403


async def test_list_filters_by_phase_group_and_status(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    await _create_doc(client, token, project_id, stt=1, phase_group="PREPARATION")
    bidding = await _create_doc(client, token, project_id, stt=2, phase_group="BIDDING")
    await _advance_to(client, token, project_id, bidding["id"], ["DRAFT_DOCX"])

    # Act
    by_phase = await client.get(
        _docs_url(project_id), params={"phase_group": "BIDDING"}, headers=_bearer(token)
    )
    by_status = await client.get(
        _docs_url(project_id), params={"maturity_status": "DRAFT_DOCX"}, headers=_bearer(token)
    )

    # Assert
    assert [doc["stt"] for doc in by_phase.json()] == [2]
    assert [doc["stt"] for doc in by_status.json()] == [2]


async def test_unknown_document_returns_404(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    missing_id = "00000000-0000-0000-0000-000000000000"

    # Act
    response = await client.get(f"{_docs_url(project_id)}/{missing_id}", headers=_bearer(token))

    # Assert
    assert response.status_code == 404


async def test_valid_transition_updates_status_and_is_audited(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    session: AsyncSession,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    doc = await _create_doc(client, token, project_id)

    # Act
    response = await _transition(
        client,
        token,
        project_id,
        doc["id"],
        {"expected_status": "MISSING", "target_status": "DRAFT_DOCX"},
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["maturity_status"] == "DRAFT_DOCX"
    audited = (
        await session.execute(
            select(AuditLog).where(AuditLog.action == "legal_document.transition")
        )
    ).scalar_one()
    assert audited.changes == {"from": "MISSING", "to": "DRAFT_DOCX"}


async def test_transition_with_stale_expected_status_returns_409(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    doc = await _create_doc(client, token, project_id)

    # Act
    response = await _transition(
        client,
        token,
        project_id,
        doc["id"],
        {"expected_status": "DRAFT_DOCX", "target_status": "SUBMITTED_REVIEW"},
    )

    # Assert
    assert response.status_code == 409


async def test_skipping_a_step_returns_409(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    doc = await _create_doc(client, token, project_id)

    # Act
    response = await _transition(
        client,
        token,
        project_id,
        doc["id"],
        {"expected_status": "MISSING", "target_status": "SUBMITTED_REVIEW"},
    )

    # Assert
    assert response.status_code == 409


async def test_backward_transition_without_reason_returns_422(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    doc = await _create_doc(client, token, project_id)
    await _advance_to(client, token, project_id, doc["id"], ["DRAFT_DOCX", "SUBMITTED_REVIEW"])

    # Act
    response = await _transition(
        client,
        token,
        project_id,
        doc["id"],
        {"expected_status": "SUBMITTED_REVIEW", "target_status": "DRAFT_DOCX"},
    )

    # Assert
    assert response.status_code == 422


async def test_backward_transition_with_reason_is_audited_with_reason(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    session: AsyncSession,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    doc = await _create_doc(client, token, project_id)
    await _advance_to(client, token, project_id, doc["id"], ["DRAFT_DOCX", "SUBMITTED_REVIEW"])

    # Act
    response = await _transition(
        client,
        token,
        project_id,
        doc["id"],
        {
            "expected_status": "SUBMITTED_REVIEW",
            "target_status": "DRAFT_DOCX",
            "reason": "Sở yêu cầu sửa tên gói thầu",
        },
    )

    # Assert
    assert response.status_code == 200
    audited = (
        (
            await session.execute(
                select(AuditLog).where(AuditLog.action == "legal_document.transition")
            )
        )
        .scalars()
        .all()
    )
    assert any(row.changes.get("reason") == "Sở yêu cầu sửa tên gói thầu" for row in audited)


async def test_verified_closed_document_cannot_be_edited_directly_returns_409(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    doc = await _create_doc(client, token, project_id)
    await _advance_to(client, token, project_id, doc["id"], CHAIN_TO_CLOSED)

    # Act
    response = await client.patch(
        f"{_docs_url(project_id)}/{doc['id']}",
        json={"notes": "sửa trực tiếp"},
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 409


async def test_reopen_verified_closed_requires_reason_and_returns_to_signed_scan(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    doc = await _create_doc(client, token, project_id)
    await _advance_to(client, token, project_id, doc["id"], CHAIN_TO_CLOSED)
    reopen_body = {"expected_status": "VERIFIED_CLOSED", "target_status": "SIGNED_SCAN_PDF"}

    # Act
    without_reason = await _transition(client, token, project_id, doc["id"], reopen_body)
    with_reason = await _transition(
        client,
        token,
        project_id,
        doc["id"],
        {**reopen_body, "reason": "Phát hiện bản scan bị mờ dấu đỏ"},
    )

    # Assert
    assert without_reason.status_code == 422
    assert with_reason.status_code == 200
    assert with_reason.json()["maturity_status"] == "SIGNED_SCAN_PDF"


async def test_summary_counts_by_status_and_phase_group(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    await _create_doc(client, token, project_id, stt=1, phase_group="PREPARATION")
    await _create_doc(client, token, project_id, stt=2, phase_group="PREPARATION")
    bidding = await _create_doc(client, token, project_id, stt=3, phase_group="BIDDING")
    await _advance_to(client, token, project_id, bidding["id"], ["DRAFT_DOCX"])

    # Act
    response = await client.get(f"{_docs_url(project_id)}/summary", headers=_bearer(token))

    # Assert
    body = response.json()
    assert response.status_code == 200
    assert body["total"] == 3
    assert body["by_status"]["MISSING"] == 2
    assert body["by_status"]["DRAFT_DOCX"] == 1
    assert body["by_status"]["VERIFIED_CLOSED"] == 0
    assert body["by_phase_group"]["PREPARATION"]["MISSING"] == 2
    assert body["by_phase_group"]["BIDDING"]["DRAFT_DOCX"] == 1


async def test_write_endpoints_return_429_after_too_many_writes(
    settings: Settings,
    make_user: UserFactory,
) -> None:
    # Arrange
    await make_user(email="pm-gioi-han-phap-ly@example.com", role=Role.PM)
    async with limited_client(
        settings,
        login_rate_limit_attempts=10,
        write_rate_limit_attempts=3,
        write_rate_limit_window_seconds=60,
    ) as client:
        token = await login_as(client, "pm-gioi-han-phap-ly@example.com")
        project_id = await create_project(client, token)

        # Act
        responses = [
            await client.post(
                _docs_url(project_id),
                json={**LEGAL_PAYLOAD, "stt": index},
                headers=_bearer(token),
            )
            for index in (1, 2, 3)
        ]

    # Assert
    assert [response.status_code for response in responses] == [201, 201, 429]
    assert int(responses[-1].headers["Retry-After"]) > 0

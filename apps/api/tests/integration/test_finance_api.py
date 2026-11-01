from datetime import date, timedelta
from decimal import Decimal

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import Role
from app.models.audit_log import AuditLog
from tests.integration.helpers import (
    CONTRACT_PAYLOAD,
    UserFactory,
    create_contract,
    create_project,
    login_as,
)

pytestmark = pytest.mark.integration

CONTRACT_VALUE = Decimal(CONTRACT_PAYLOAD["contract_value"])
RULE_PAYLOAD = {
    "guarantee_percent": "3.00",
    "advance_ceiling_percent": "30.00",
    "advance_working_days": 20,
    "lock_on": "2026-12-09",
    "lock_warning_days": 15,
    "non_working_days": [],
    "effective_from": "2000-01-01",
}
GUARANTEE_PAYLOAD = {
    "issued_on": "2026-02-01",
    "expires_on": "2026-06-01",
    "poa_expires_on": "2026-05-01",
}
DISBURSEMENT_PLAN = {"plan_year": 2026, "planned_amount": "200.00"}


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _pm_with_project_and_contract(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> tuple[str, str, str]:
    await make_user(email="pm@example.com", role=Role.PM)
    token = await login_as(client, "pm@example.com")
    project_id = await create_project(client, token)
    contract_id = await create_contract(client, token, project_id)
    return token, project_id, contract_id


async def _create_finance_rule(
    client: httpx.AsyncClient,
    token: str,
    project_id: str,
    **overrides: object,
) -> None:
    response = await client.post(
        f"/api/v1/projects/{project_id}/finance-rules",
        json={**RULE_PAYLOAD, **overrides},
        headers=_bearer(token),
    )
    assert response.status_code == 201, response.text


async def test_guarantee_is_three_percent_of_base_contract_value(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id, contract_id = await _pm_with_project_and_contract(client, make_user)
    await _create_finance_rule(client, token, project_id)

    # Act
    response = await client.post(
        f"/api/v1/projects/{project_id}/contracts/{contract_id}/guarantees",
        json=GUARANTEE_PAYLOAD,
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 201, response.text
    assert Decimal(response.json()["amount"]) == CONTRACT_VALUE * Decimal("0.03")
    assert response.json()["poa_expired_before_issue"] is False


async def test_guarantee_without_effective_rule_returns_422(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id, contract_id = await _pm_with_project_and_contract(client, make_user)

    # Act
    response = await client.post(
        f"/api/v1/projects/{project_id}/contracts/{contract_id}/guarantees",
        json=GUARANTEE_PAYLOAD,
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 422


async def test_guarantee_flags_poa_expiring_before_issue_date(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id, contract_id = await _pm_with_project_and_contract(client, make_user)
    await _create_finance_rule(client, token, project_id)

    # Act
    response = await client.post(
        f"/api/v1/projects/{project_id}/contracts/{contract_id}/guarantees",
        json={**GUARANTEE_PAYLOAD, "poa_expires_on": "2026-01-31"},
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 201, response.text
    assert response.json()["poa_expired_before_issue"] is True


async def test_guarantee_creation_is_audited_with_actor(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    session: AsyncSession,
) -> None:
    # Arrange
    token, project_id, contract_id = await _pm_with_project_and_contract(client, make_user)
    await _create_finance_rule(client, token, project_id)

    # Act
    await client.post(
        f"/api/v1/projects/{project_id}/contracts/{contract_id}/guarantees",
        json=GUARANTEE_PAYLOAD,
        headers=_bearer(token),
    )

    # Assert
    audited = (
        await session.execute(select(AuditLog).where(AuditLog.action == "guarantee.create"))
    ).scalar_one()
    assert audited.actor_id is not None


async def test_advance_above_ceiling_returns_409(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id, contract_id = await _pm_with_project_and_contract(client, make_user)
    await _create_finance_rule(client, token, project_id)
    ceiling = CONTRACT_VALUE * Decimal("0.30")
    advance_url = f"/api/v1/projects/{project_id}/contracts/{contract_id}/advances"
    await client.post(
        advance_url,
        json={
            "amount": str(ceiling),
            "complete_packet_on": "2026-02-02",
            "decided_on": "2026-02-02",
        },
        headers=_bearer(token),
    )

    # Act
    response = await client.post(
        advance_url,
        json={
            "amount": "0.01",
            "complete_packet_on": "2026-02-02",
            "decided_on": "2026-02-02",
        },
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 409


async def test_advance_decided_on_twenty_first_working_day_is_flagged_late(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id, contract_id = await _pm_with_project_and_contract(client, make_user)
    await _create_finance_rule(client, token, project_id)

    # Act
    response = await client.post(
        f"/api/v1/projects/{project_id}/contracts/{contract_id}/advances",
        json={
            "amount": "1.00",
            "complete_packet_on": "2026-11-02",
            "decided_on": "2026-12-01",
        },
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 201, response.text
    assert response.json()["on_time"] is False


async def test_disbursement_payment_updates_rate_and_flags_overrun_without_rejecting(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id, contract_id = await _pm_with_project_and_contract(client, make_user)
    plan = await client.post(
        f"/api/v1/projects/{project_id}/disbursements",
        json={"contract_id": contract_id, **DISBURSEMENT_PLAN},
        headers=_bearer(token),
    )
    disbursement_id = plan.json()["id"]
    payment_url = f"/api/v1/projects/{project_id}/disbursements/{disbursement_id}/payments"

    # Act
    await client.post(
        payment_url,
        json={"amount": "50.00", "paid_on": "2026-03-01"},
        headers=_bearer(token),
    )
    response = await client.post(
        payment_url,
        json={"amount": "200.00", "paid_on": "2026-04-01"},
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 200, response.text
    assert Decimal(response.json()["paid_amount"]) == Decimal("250.00")
    assert Decimal(response.json()["rate_percent"]) == Decimal("125.00")
    assert response.json()["exceeds_plan"] is True


async def test_duplicate_disbursement_for_same_contract_and_year_returns_409(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id, contract_id = await _pm_with_project_and_contract(client, make_user)
    url = f"/api/v1/projects/{project_id}/disbursements"
    await client.post(
        url, json={"contract_id": contract_id, **DISBURSEMENT_PLAN}, headers=_bearer(token)
    )

    # Act
    response = await client.post(
        url, json={"contract_id": contract_id, **DISBURSEMENT_PLAN}, headers=_bearer(token)
    )

    # Assert
    assert response.status_code == 409


async def test_lock_warning_is_active_when_lock_date_is_within_warn_days(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id, contract_id = await _pm_with_project_and_contract(client, make_user)
    lock_on = date.today() + timedelta(days=10)
    await _create_finance_rule(client, token, project_id, lock_on=lock_on.isoformat())
    await client.post(
        f"/api/v1/projects/{project_id}/disbursements",
        json={"contract_id": contract_id, **DISBURSEMENT_PLAN},
        headers=_bearer(token),
    )

    # Act
    response = await client.get(
        f"/api/v1/projects/{project_id}/disbursements", headers=_bearer(token)
    )

    # Assert
    assert response.status_code == 200, response.text
    row = response.json()[0]
    assert row["lock_warning_active"] is True
    assert row["days_to_lock"] == 10


async def test_finance_rule_with_duplicate_effective_date_returns_409(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id, _contract_id = await _pm_with_project_and_contract(client, make_user)
    await _create_finance_rule(client, token, project_id)

    # Act
    response = await client.post(
        f"/api/v1/projects/{project_id}/finance-rules",
        json=RULE_PAYLOAD,
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 409


async def test_consultant_cannot_create_finance_rule(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id, _contract_id = await _pm_with_project_and_contract(client, make_user)
    await make_user(email="consultant@example.com", role=Role.PM_CONSULTANT)
    consultant_token = await login_as(client, "consultant@example.com")

    # Act
    response = await client.post(
        f"/api/v1/projects/{project_id}/finance-rules",
        json={**RULE_PAYLOAD, "effective_from": "2001-01-01"},
        headers=_bearer(consultant_token),
    )

    # Assert
    assert response.status_code == 403


async def test_guarantee_for_contract_of_another_project_returns_404(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id, _contract_id = await _pm_with_project_and_contract(client, make_user)
    await _create_finance_rule(client, token, project_id)
    other_project_id = await create_project(client, token, code="SGD-HCM-OTHER-2026")
    other_contract_id = await create_contract(client, token, other_project_id)

    # Act
    response = await client.post(
        f"/api/v1/projects/{project_id}/contracts/{other_contract_id}/guarantees",
        json=GUARANTEE_PAYLOAD,
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 404

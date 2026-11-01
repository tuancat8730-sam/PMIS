from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.disbursement_rules import (
    days_until,
    disbursement_rate,
    exceeds_plan,
    lock_warning_active,
)
from app.models.disbursement import Disbursement
from app.models.finance_rule import FinanceRule
from app.schemas.finance import DisbursementCreate, DisbursementOut, DisbursementPaymentCreate


class DuplicateDisbursementError(Exception):
    """Hợp đồng đã có kế hoạch vốn cho năm này."""


async def create_disbursement(
    session: AsyncSession,
    *,
    project_id: UUID,
    payload: DisbursementCreate,
) -> Disbursement:
    disbursement = Disbursement(
        project_id=project_id,
        contract_id=payload.contract_id,
        plan_year=payload.plan_year,
        planned_amount=payload.planned_amount,
    )
    session.add(disbursement)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise DuplicateDisbursementError(str(payload.plan_year)) from exc
    return disbursement


async def list_disbursements(session: AsyncSession, project_id: UUID) -> list[Disbursement]:
    result = await session.execute(
        select(Disbursement)
        .where(Disbursement.project_id == project_id)
        .order_by(Disbursement.plan_year.desc())
    )
    return list(result.scalars().all())


async def get_disbursement(
    session: AsyncSession,
    project_id: UUID,
    disbursement_id: UUID,
) -> Disbursement | None:
    result = await session.execute(
        select(Disbursement).where(
            Disbursement.id == disbursement_id,
            Disbursement.project_id == project_id,
        )
    )
    return result.scalar_one_or_none()


async def record_payment(
    session: AsyncSession,
    *,
    disbursement: Disbursement,
    payload: DisbursementPaymentCreate,
) -> Disbursement:
    """Cộng số tiền vừa giải ngân. Vượt kế hoạch chỉ được cảnh báo, không chặn."""
    disbursement.paid_amount = disbursement.paid_amount + payload.amount
    disbursement.paid_on = payload.paid_on
    if payload.packet_status is not None:
        disbursement.packet_status = payload.packet_status
    await session.flush()
    return disbursement


def disbursement_out(
    disbursement: Disbursement,
    rule: FinanceRule | None,
    today: date,
) -> DisbursementOut:
    """Chiếu một dòng giải ngân kèm tỷ lệ và đếm ngược khóa sổ theo ngưỡng có hiệu lực hôm nay."""
    return DisbursementOut(
        id=disbursement.id,
        project_id=disbursement.project_id,
        contract_id=disbursement.contract_id,
        plan_year=disbursement.plan_year,
        planned_amount=disbursement.planned_amount,
        paid_amount=disbursement.paid_amount,
        paid_on=disbursement.paid_on,
        packet_status=disbursement.packet_status,
        rate_percent=disbursement_rate(disbursement.paid_amount, disbursement.planned_amount),
        exceeds_plan=exceeds_plan(disbursement.paid_amount, disbursement.planned_amount),
        lock_warning_active=(
            rule is not None and lock_warning_active(rule.lock_on, today, rule.lock_warning_days)
        ),
        days_to_lock=days_until(rule.lock_on, today) if rule is not None else None,
    )

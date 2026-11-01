from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.advance_rules import advance_within_ceiling, is_advance_on_time
from app.core.guarantee_rules import guarantee_amount
from app.models.contract import Contract
from app.models.contract_advance import ContractAdvance
from app.models.contract_guarantee import ContractGuarantee
from app.models.finance_rule import FinanceRule
from app.schemas.finance import AdvanceCreate, FinanceRuleCreate, GuaranteeCreate


class DuplicateFinanceRuleError(Exception):
    """Đã có ngưỡng tài chính với ngày hiệu lực này trong dự án."""


class AdvanceCeilingExceededError(Exception):
    """Tổng tạm ứng sau khi cộng khoản mới vượt trần tỷ lệ của hợp đồng."""


async def list_finance_rules(session: AsyncSession, project_id: UUID) -> list[FinanceRule]:
    result = await session.execute(
        select(FinanceRule)
        .where(FinanceRule.project_id == project_id)
        .order_by(FinanceRule.effective_from.desc())
    )
    return list(result.scalars().all())


async def create_finance_rule(
    session: AsyncSession,
    *,
    project_id: UUID,
    payload: FinanceRuleCreate,
) -> FinanceRule:
    rule = FinanceRule(project_id=project_id, **payload.model_dump())
    session.add(rule)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise DuplicateFinanceRuleError(str(payload.effective_from)) from exc
    return rule


async def effective_finance_rule(
    session: AsyncSession,
    project_id: UUID,
    on: date,
) -> FinanceRule | None:
    """Ngưỡng có hiệu lực vào ngày `on`: bản ghi có ngày hiệu lực gần nhất không vượt quá `on`."""
    result = await session.execute(
        select(FinanceRule)
        .where(FinanceRule.project_id == project_id, FinanceRule.effective_from <= on)
        .order_by(FinanceRule.effective_from.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def create_guarantee(
    session: AsyncSession,
    *,
    contract: Contract,
    rule: FinanceRule,
    payload: GuaranteeCreate,
) -> ContractGuarantee:
    """Chụp giá trị gốc của hợp đồng vào bảo lãnh, để phụ lục sau này không làm đổi số tiền."""
    guarantee = ContractGuarantee(
        contract_id=contract.id,
        base_contract_value=contract.contract_value,
        percent=rule.guarantee_percent,
        amount=guarantee_amount(contract.contract_value, rule.guarantee_percent),
        issued_on=payload.issued_on,
        expires_on=payload.expires_on,
        poa_expires_on=payload.poa_expires_on,
    )
    session.add(guarantee)
    await session.flush()
    return guarantee


async def list_guarantees(session: AsyncSession, contract_id: UUID) -> list[ContractGuarantee]:
    result = await session.execute(
        select(ContractGuarantee)
        .where(ContractGuarantee.contract_id == contract_id)
        .order_by(ContractGuarantee.issued_on.desc())
    )
    return list(result.scalars().all())


async def total_advanced(session: AsyncSession, contract_id: UUID) -> Decimal:
    result = await session.execute(
        select(func.coalesce(func.sum(ContractAdvance.amount), Decimal("0"))).where(
            ContractAdvance.contract_id == contract_id
        )
    )
    return result.scalar_one()


async def create_advance(
    session: AsyncSession,
    *,
    contract: Contract,
    rule: FinanceRule,
    payload: AdvanceCreate,
) -> ContractAdvance:
    """Khóa dòng hợp đồng trước khi cộng dồn, để hai tạm ứng song song không cùng vượt trần."""
    await session.execute(select(Contract.id).where(Contract.id == contract.id).with_for_update())
    granted = await total_advanced(session, contract.id)
    if not advance_within_ceiling(
        contract_value=contract.contract_value,
        ceiling_percent=rule.advance_ceiling_percent,
        already_granted=granted,
        requested=payload.amount,
    ):
        raise AdvanceCeilingExceededError(str(granted))

    advance = ContractAdvance(
        contract_id=contract.id,
        amount=payload.amount,
        complete_packet_on=payload.complete_packet_on,
        decided_on=payload.decided_on,
        on_time=is_advance_on_time(
            payload.complete_packet_on,
            payload.decided_on,
            rule.advance_working_days,
            rule.non_working_days,
        ),
    )
    session.add(advance)
    await session.flush()
    return advance


async def list_advances(session: AsyncSession, contract_id: UUID) -> list[ContractAdvance]:
    result = await session.execute(
        select(ContractAdvance)
        .where(ContractAdvance.contract_id == contract_id)
        .order_by(ContractAdvance.decided_on.desc())
    )
    return list(result.scalars().all())

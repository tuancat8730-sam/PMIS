from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contract import Contract
from app.schemas.contracts import ContractCreate


async def create_contract(
    session: AsyncSession,
    *,
    project_id: UUID,
    payload: ContractCreate,
) -> Contract:
    contract = Contract(project_id=project_id, **payload.model_dump())
    session.add(contract)
    await session.flush()
    return contract


async def get_contract(session: AsyncSession, contract_id: UUID) -> Contract | None:
    return await session.get(Contract, contract_id)


async def get_project_contract(
    session: AsyncSession,
    project_id: UUID,
    contract_id: UUID,
) -> Contract | None:
    """Hợp đồng chỉ coi là tồn tại khi thuộc đúng dự án đang truy cập."""
    contract = await get_contract(session, contract_id)
    if contract is None or contract.project_id != project_id:
        return None
    return contract


async def list_contracts(session: AsyncSession, project_id: UUID) -> list[Contract]:
    result = await session.execute(
        select(Contract).where(Contract.project_id == project_id).order_by(Contract.package_name)
    )
    return list(result.scalars().all())

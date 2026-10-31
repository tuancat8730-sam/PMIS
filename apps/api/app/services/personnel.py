from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import FieldCipher
from app.models.contract import Contract
from app.models.contract_personnel import ContractPersonnel, PersonnelComplianceStatus
from app.schemas.personnel import PersonnelCreate

CCCD_LAST_DIGITS = 4


async def _project_cccd_values(
    session: AsyncSession,
    project_id: UUID,
    cipher: FieldCipher,
) -> list[str]:
    """Giải mã CCCD của mọi nhân sự trong dự án để so khớp trùng. Quy mô dự án nhỏ nên chấp nhận."""
    result = await session.execute(
        select(ContractPersonnel.national_id_encrypted)
        .join(Contract, Contract.id == ContractPersonnel.contract_id)
        .where(
            Contract.project_id == project_id,
            ContractPersonnel.national_id_encrypted.is_not(None),
        )
    )
    return [cipher.decrypt(token) for token in result.scalars().all() if token is not None]


async def create_personnel(
    session: AsyncSession,
    *,
    contract: Contract,
    payload: PersonnelCreate,
    cipher: FieldCipher,
) -> ContractPersonnel:
    cccd = payload.national_id_cccd
    compliance_status = PersonnelComplianceStatus.VERIFIED
    encrypted_cccd: str | None = None
    last_four: str | None = None

    if cccd is not None:
        known_values = await _project_cccd_values(session, contract.project_id, cipher)
        if cccd in known_values:
            compliance_status = PersonnelComplianceStatus.DUPLICATE_ID_WARNING
        encrypted_cccd = cipher.encrypt(cccd)
        last_four = cccd[-CCCD_LAST_DIGITS:]

    personnel = ContractPersonnel(
        contract_id=contract.id,
        national_id_encrypted=encrypted_cccd,
        national_id_last4=last_four,
        compliance_status=compliance_status,
        **payload.model_dump(exclude={"national_id_cccd"}),
    )
    session.add(personnel)
    await session.flush()
    return personnel


async def list_personnel(session: AsyncSession, contract_id: UUID) -> list[ContractPersonnel]:
    result = await session.execute(
        select(ContractPersonnel)
        .where(ContractPersonnel.contract_id == contract_id)
        .order_by(ContractPersonnel.full_name)
    )
    return list(result.scalars().all())

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import CipherDep, SessionDep, WriteRateLimitDep, contract_role_guard
from app.core.rbac import Principal, Role, get_current_principal
from app.models.contract import Contract
from app.models.contract_personnel import ContractPersonnel
from app.schemas.personnel import PersonnelCreate, PersonnelOut
from app.services.audit import record_audit
from app.services.personnel import create_personnel, list_personnel

router = APIRouter(prefix="/contracts/{contract_id}/personnel", tags=["personnel"])

# Nhân sự chứa CCCD (PII): chỉ PM của dự án (hoặc ADMIN) được đọc hoặc ghi.
PERSONNEL_ROLE = Role.PM


@router.post("", response_model=PersonnelOut, status_code=status.HTTP_201_CREATED)
async def create_personnel_endpoint(
    payload: PersonnelCreate,
    contract: Annotated[Contract, Depends(contract_role_guard(PERSONNEL_ROLE))],
    cipher: CipherDep,
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> ContractPersonnel:
    personnel = await create_personnel(
        session,
        contract=contract,
        payload=payload,
        cipher=cipher,
    )

    await record_audit(
        session,
        actor_id=principal.user_id,
        action="personnel.create",
        entity_type="contract_personnel",
        entity_id=str(personnel.id),
        changes={
            "position_role": personnel.position_role,
            "compliance_status": personnel.compliance_status.value,
        },
    )
    await session.commit()
    return personnel


@router.get("", response_model=list[PersonnelOut])
async def list_personnel_endpoint(
    contract: Annotated[Contract, Depends(contract_role_guard(PERSONNEL_ROLE))],
    session: SessionDep,
) -> list[ContractPersonnel]:
    return await list_personnel(session, contract.id)

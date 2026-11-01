from fastapi import APIRouter

from app.api.v1 import (
    auth,
    beneficiary_units,
    contracts,
    delivery_handovers,
    disbursements,
    drive,
    drive_uploads,
    equipment,
    field,
    finance,
    health,
    hold_points,
    it_system,
    it_system_quality,
    legal_documents,
    milestones,
    penalties,
    personnel,
    project_members,
    projects,
    risk_issues,
    stakeholders,
    users,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(projects.router)
api_router.include_router(project_members.router)
api_router.include_router(stakeholders.router)
api_router.include_router(contracts.router)
api_router.include_router(personnel.router)
api_router.include_router(beneficiary_units.router)
api_router.include_router(milestones.router)
api_router.include_router(hold_points.router)
api_router.include_router(penalties.router)
api_router.include_router(finance.router)
api_router.include_router(equipment.router)
api_router.include_router(delivery_handovers.router)
api_router.include_router(field.router)
api_router.include_router(disbursements.router)
api_router.include_router(risk_issues.router)
api_router.include_router(it_system.router)
api_router.include_router(it_system_quality.router)
api_router.include_router(legal_documents.router)
api_router.include_router(drive.router)
api_router.include_router(drive_uploads.router)

from fastapi import APIRouter

from app.api.v1 import (
    auth,
    contracts,
    health,
    personnel,
    project_members,
    projects,
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

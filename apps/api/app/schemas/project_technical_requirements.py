from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ProjectTechnicalRequirementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    sort_order: int
    item: str
    standard: str | None
    legal_basis: str | None
    solution: str | None
    responsibility: str | None
    acceptance_criteria: str | None
    related_risk: str | None
    monitoring_status: str | None

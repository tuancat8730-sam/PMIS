from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.core.contract_countdown import CountdownStatus
from app.models.project import ProjectHealth


class CommandCenterKpi(BaseModel):
    contract_value_by_kind: dict[str, Decimal]
    contract_value_total: Decimal
    running_project_count: int
    beneficiary_unit_count: int
    # Hồ sơ chờ ký cần E4; chưa có dữ liệu thì để null, không hiển thị số giả.
    pending_signature_count: None = None
    red_alert_count: int


class ProjectHealthRow(BaseModel):
    id: UUID
    code: str
    short_name: str
    health: ProjectHealth
    red_alert_count: int
    max_slippage_days: int


class RedAlertRow(BaseModel):
    project_code: str
    source: Literal["MILESTONE", "RISK"]
    code: str
    title: str
    due_date: date


class ContractCountdownRow(BaseModel):
    project_code: str
    contract_number: str | None
    status: CountdownStatus
    expiration_date: date
    days_remaining: int


class CommandCenterOut(BaseModel):
    as_of: date
    kpi: CommandCenterKpi
    projects: list[ProjectHealthRow]
    red_alerts: list[RedAlertRow]
    contract_countdowns: list[ContractCountdownRow]

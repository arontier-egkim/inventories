from pydantic import BaseModel


class OvertimeRequestCreate(BaseModel):
    date: str
    type: str = "OVERTIME"
    planned_start: str
    planned_end: str
    planned_hours: float
    reason: str | None = None


class OvertimeRequestResponse(BaseModel):
    id: str
    user_id: str
    user_name: str | None = None
    date: str
    type: str
    planned_start: str
    planned_end: str
    planned_hours: float
    reason: str | None = None
    status: str
    approver_id: str | None = None
    approver_name: str | None = None
    created_at: str

    model_config = {"from_attributes": True}


class WeeklyWorkSummaryResponse(BaseModel):
    id: str
    user_id: str
    year: int
    week_number: int
    regular_hours: float
    overtime_hours: float
    total_hours: float
    is_exceeded: bool

    model_config = {"from_attributes": True}

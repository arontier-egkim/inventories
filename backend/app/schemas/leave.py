from pydantic import BaseModel


class LeaveTypeResponse(BaseModel):
    id: str
    name: str
    code: str
    is_paid: bool
    is_deductible: bool
    deduction_days: float
    default_days: float
    description: str | None = None

    model_config = {"from_attributes": True}


class LeaveBalanceResponse(BaseModel):
    id: str
    user_id: str
    leave_type_id: str
    leave_type_name: str | None = None
    year: int
    total_days: float
    used_days: float
    remaining_days: float = 0.0

    model_config = {"from_attributes": True}


class LeaveRequestCreate(BaseModel):
    leave_type_id: str
    start_date: str
    end_date: str
    days: float
    reason: str | None = None


class LeaveRequestResponse(BaseModel):
    id: str
    user_id: str
    user_name: str | None = None
    leave_type_id: str
    leave_type_name: str | None = None
    start_date: str
    end_date: str
    days: float
    reason: str | None = None
    status: str
    approver_id: str | None = None
    approver_name: str | None = None
    created_at: str

    model_config = {"from_attributes": True}

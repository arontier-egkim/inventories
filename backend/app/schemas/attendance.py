from pydantic import BaseModel


class CheckInRequest(BaseModel):
    note: str | None = None


class CheckOutRequest(BaseModel):
    note: str | None = None


class AttendanceResponse(BaseModel):
    id: str
    user_id: str
    date: str
    check_in_at: str | None = None
    check_out_at: str | None = None
    work_minutes: int | None = None
    status: str
    note: str | None = None
    created_at: str

    model_config = {"from_attributes": True}


class HolidayCreate(BaseModel):
    date: str
    name: str
    type: str = "PUBLIC"
    year: int


class HolidayResponse(BaseModel):
    id: str
    date: str
    name: str
    type: str
    year: int

    model_config = {"from_attributes": True}

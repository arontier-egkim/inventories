from pydantic import BaseModel


class DepartmentBase(BaseModel):
    name: str
    code: str
    parent_id: str | None = None
    level: int = 0
    sort_order: int = 0
    is_active: bool = True


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    parent_id: str | None = None
    level: int | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class DepartmentResponse(DepartmentBase):
    id: str
    created_at: str
    updated_at: str
    children: list["DepartmentResponse"] = []

    model_config = {"from_attributes": True}


class PositionResponse(BaseModel):
    id: str
    name: str
    level: int
    sort_order: int

    model_config = {"from_attributes": True}


class TitleResponse(BaseModel):
    id: str
    name: str
    level: int
    sort_order: int

    model_config = {"from_attributes": True}


class UserDepartmentAssign(BaseModel):
    department_id: str
    position_id: str | None = None
    title_id: str | None = None
    is_primary: bool = True
    start_date: str | None = None


class OrgChartNode(BaseModel):
    department: DepartmentResponse
    members: list[dict] = []
    children: list["OrgChartNode"] = []

    model_config = {"from_attributes": True}

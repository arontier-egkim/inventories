from pydantic import BaseModel


class UserBase(BaseModel):
    email: str
    name: str
    employee_number: str | None = None
    phone: str | None = None
    hire_date: str | None = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    profile_image_url: str | None = None
    hire_date: str | None = None
    status: str | None = None
    is_active: bool | None = None
    employee_number: str | None = None


class UserDepartmentInfo(BaseModel):
    department_id: str
    department_name: str
    position_id: str | None = None
    position_name: str | None = None
    title_id: str | None = None
    title_name: str | None = None
    is_primary: bool = True

    model_config = {"from_attributes": True}


class UserRoleInfo(BaseModel):
    role_id: str
    role_name: str
    role_code: str

    model_config = {"from_attributes": True}


class UserResponse(UserBase):
    id: str
    profile_image_url: str | None = None
    status: str
    is_active: bool
    must_change_password: bool
    last_login_at: str | None = None
    created_at: str
    updated_at: str
    departments: list[UserDepartmentInfo] = []
    roles: list[UserRoleInfo] = []

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    id: str
    email: str
    name: str
    employee_number: str | None = None
    phone: str | None = None
    status: str
    is_active: bool
    created_at: str

    model_config = {"from_attributes": True}

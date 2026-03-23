from pydantic import BaseModel


class RoleBase(BaseModel):
    name: str
    code: str
    description: str | None = None
    is_system: bool = False


class RoleCreate(RoleBase):
    pass


class PermissionResponse(BaseModel):
    id: str
    name: str
    code: str
    resource: str
    action: str
    description: str | None = None

    model_config = {"from_attributes": True}


class RoleResponse(RoleBase):
    id: str
    created_at: str
    permissions: list[PermissionResponse] = []

    model_config = {"from_attributes": True}


class RolePermissionUpdate(BaseModel):
    permission_ids: list[str]


class UserRoleUpdate(BaseModel):
    role_ids: list[str]

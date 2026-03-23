from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.role import Role, Permission, RolePermission, UserRole
from app.schemas.role import RoleCreate, RoleResponse, PermissionResponse, RolePermissionUpdate, UserRoleUpdate

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get("", response_model=list[RoleResponse])
def list_roles(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    roles = db.query(Role).all()
    result = []
    for role in roles:
        perms = []
        for rp in role.permissions:
            perms.append(PermissionResponse.model_validate(rp.permission))
        result.append(RoleResponse(
            id=role.id, name=role.name, code=role.code,
            description=role.description, is_system=role.is_system,
            created_at=role.created_at, permissions=perms,
        ))
    return result


@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(body: RoleCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    role = Role(**body.model_dump())
    db.add(role)
    db.commit()
    db.refresh(role)
    return RoleResponse(
        id=role.id, name=role.name, code=role.code,
        description=role.description, is_system=role.is_system,
        created_at=role.created_at, permissions=[],
    )


@router.put("/{role_id}/permissions")
def update_role_permissions(
    role_id: str,
    body: RolePermissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    db.query(RolePermission).filter(RolePermission.role_id == role_id).delete()
    for perm_id in body.permission_ids:
        db.add(RolePermission(role_id=role_id, permission_id=perm_id))
    db.commit()
    return {"message": "Permissions updated"}



from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.core.security import hash_password
from app.models.user import User
from app.models.role import UserRole
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse, UserDepartmentInfo, UserRoleInfo
from app.schemas.role import UserRoleUpdate

router = APIRouter(prefix="/users", tags=["Users"])


def _build_user_response(user: User) -> UserResponse:
    dept_infos = []
    for ud in user.departments:
        dept_infos.append(UserDepartmentInfo(
            department_id=ud.department_id,
            department_name=ud.department.name if ud.department else "",
            position_id=ud.position_id,
            position_name=ud.position.name if ud.position else None,
            title_id=ud.title_id,
            title_name=ud.title.name if ud.title else None,
            is_primary=ud.is_primary,
        ))
    role_infos = []
    for ur in user.roles:
        role_infos.append(UserRoleInfo(
            role_id=ur.role_id,
            role_name=ur.role.name,
            role_code=ur.role.code,
        ))
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        employee_number=user.employee_number,
        phone=user.phone,
        profile_image_url=user.profile_image_url,
        hire_date=user.hire_date,
        status=user.status,
        is_active=user.is_active,
        must_change_password=user.must_change_password,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
        departments=dept_infos,
        roles=role_infos,
    )


@router.get("", response_model=list[UserListResponse])
def list_users(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    users = db.query(User).filter(User.deleted_at.is_(None)).offset(skip).limit(limit).all()
    return [UserListResponse.model_validate(u) for u in users]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        name=body.name,
        employee_number=body.employee_number,
        phone=body.phone,
        hire_date=body.hire_date,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _build_user_response(user)


@router.get("/search", response_model=list[UserListResponse])
def search_users(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    users = db.query(User).filter(
        User.deleted_at.is_(None),
        (User.name.contains(q) | User.email.contains(q) | User.employee_number.contains(q)),
    ).limit(20).all()
    return [UserListResponse.model_validate(u) for u in users]


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _build_user_response(user)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    body: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return _build_user_response(user)


@router.put("/{user_id}/roles")
def update_user_roles(
    user_id: str,
    body: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.query(UserRole).filter(UserRole.user_id == user_id).delete()
    for role_id in body.role_ids:
        db.add(UserRole(user_id=user_id, role_id=role_id))
    db.commit()
    return {"message": "Roles updated"}

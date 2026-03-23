from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    blacklist_token,
    hash_password,
)
from app.core.config import settings
from app.models.user import User, RefreshToken
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest
from app.schemas.user import UserResponse, UserDepartmentInfo, UserRoleInfo

router = APIRouter(prefix="/auth", tags=["Auth"])
security_scheme = HTTPBearer()


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    expires_at = (datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)).isoformat()
    db_token = RefreshToken(user_id=user.id, token=refresh_token, expires_at=expires_at)
    db.add(db_token)

    user.last_login_at = datetime.now(timezone.utc).isoformat()
    db.commit()

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db),
):
    token = credentials.credentials
    blacklist_token(token)
    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(body: RefreshRequest, db: Session = Depends(get_db)):
    payload = decode_token(body.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    db_token = db.query(RefreshToken).filter(
        RefreshToken.token == body.refresh_token,
        RefreshToken.revoked_at.is_(None),
    ).first()

    if not db_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token not found or revoked")

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # Revoke old token
    db_token.revoked_at = datetime.now(timezone.utc).isoformat()

    # Create new tokens
    new_access = create_access_token(user.id)
    new_refresh = create_refresh_token(user.id)

    expires_at = (datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)).isoformat()
    new_db_token = RefreshToken(user_id=user.id, token=new_refresh, expires_at=expires_at)
    db.add(new_db_token)
    db.commit()

    return TokenResponse(access_token=new_access, refresh_token=new_refresh)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    dept_infos = []
    for ud in current_user.departments:
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
    for ur in current_user.roles:
        role_infos.append(UserRoleInfo(
            role_id=ur.role_id,
            role_name=ur.role.name,
            role_code=ur.role.code,
        ))

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        employee_number=current_user.employee_number,
        phone=current_user.phone,
        profile_image_url=current_user.profile_image_url,
        hire_date=current_user.hire_date,
        status=current_user.status,
        is_active=current_user.is_active,
        must_change_password=current_user.must_change_password,
        last_login_at=current_user.last_login_at,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        departments=dept_infos,
        roles=role_infos,
    )

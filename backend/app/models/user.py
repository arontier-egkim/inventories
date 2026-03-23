from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    employee_number: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    profile_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    hire_date: Mapped[str | None] = mapped_column(String(10), nullable=True)  # YYYY-MM-DD
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")  # ACTIVE, ON_LEAVE, RESIGNED
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login_at: Mapped[str | None] = mapped_column(String(30), nullable=True)

    created_at: Mapped[str] = mapped_column(String(30), default=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Mapped[str] = mapped_column(String(30), default=lambda: datetime.now(timezone.utc).isoformat(), onupdate=lambda: datetime.now(timezone.utc).isoformat())
    deleted_at: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Relationships
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    departments: Mapped[list["UserDepartment"]] = relationship("UserDepartment", back_populates="user", cascade="all, delete-orphan")
    roles: Mapped[list["UserRole"]] = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    token: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    expires_at: Mapped[str] = mapped_column(String(30), nullable=False)
    revoked_at: Mapped[str | None] = mapped_column(String(30), nullable=True)

    created_at: Mapped[str] = mapped_column(String(30), default=lambda: datetime.now(timezone.utc).isoformat())

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")


# Import here to avoid circular imports — these are used in relationship strings
from app.models.organization import UserDepartment  # noqa: E402, F401
from app.models.role import UserRole  # noqa: E402, F401

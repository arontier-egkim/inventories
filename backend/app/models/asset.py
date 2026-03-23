from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, Integer, Text, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AssetCategory(Base):
    __tablename__ = "asset_categories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    parent_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("asset_categories.id"), nullable=True)
    level: Mapped[int] = mapped_column(Integer, default=0)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[str] = mapped_column(String(30), default=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Mapped[str] = mapped_column(String(30), default=lambda: datetime.now(timezone.utc).isoformat(), onupdate=lambda: datetime.now(timezone.utc).isoformat())

    parent: Mapped["AssetCategory | None"] = relationship("AssetCategory", remote_side="AssetCategory.id", backref="children")


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    asset_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    category_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("asset_categories.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    manufacturer: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    spec_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    purchase_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    purchase_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="AVAILABLE")  # IN_USE, AVAILABLE, IN_REPAIR, DISPOSED
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[str] = mapped_column(String(30), default=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Mapped[str] = mapped_column(String(30), default=lambda: datetime.now(timezone.utc).isoformat(), onupdate=lambda: datetime.now(timezone.utc).isoformat())
    deleted_at: Mapped[str | None] = mapped_column(String(30), nullable=True)

    category: Mapped["AssetCategory | None"] = relationship()
    histories: Mapped[list["AssetHistory"]] = relationship(back_populates="asset", cascade="all, delete-orphan")
    assignments: Mapped[list["AssetAssignment"]] = relationship(back_populates="asset", cascade="all, delete-orphan")


class AssetHistory(Base):
    __tablename__ = "asset_histories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    asset_id: Mapped[str] = mapped_column(String(36), ForeignKey("assets.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    from_value: Mapped[str | None] = mapped_column(String(200), nullable=True)
    to_value: Mapped[str | None] = mapped_column(String(200), nullable=True)
    performed_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    performed_at: Mapped[str] = mapped_column(String(30), default=lambda: datetime.now(timezone.utc).isoformat())
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[str] = mapped_column(String(30), default=lambda: datetime.now(timezone.utc).isoformat())

    asset: Mapped["Asset"] = relationship(back_populates="histories")
    performer: Mapped["User"] = relationship("User")


class AssetAssignment(Base):
    __tablename__ = "asset_assignments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    asset_id: Mapped[str] = mapped_column(String(36), ForeignKey("assets.id"), nullable=False)
    assignee_type: Mapped[str] = mapped_column(String(20), nullable=False)  # USER, DEPARTMENT
    assignee_id: Mapped[str] = mapped_column(String(36), nullable=False)
    assigned_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    assigned_at: Mapped[str] = mapped_column(String(30), default=lambda: datetime.now(timezone.utc).isoformat())
    returned_at: Mapped[str | None] = mapped_column(String(30), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[str] = mapped_column(String(30), default=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Mapped[str] = mapped_column(String(30), default=lambda: datetime.now(timezone.utc).isoformat(), onupdate=lambda: datetime.now(timezone.utc).isoformat())

    asset: Mapped["Asset"] = relationship(back_populates="assignments")
    assigner: Mapped["User"] = relationship("User")


from app.models.user import User  # noqa: E402, F401

from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DocumentTemplate(Base):
    __tablename__ = "document_templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fields_schema_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[str] = mapped_column(String(30), default=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Mapped[str] = mapped_column(String(30), default=lambda: datetime.now(timezone.utc).isoformat(), onupdate=lambda: datetime.now(timezone.utc).isoformat())


class ApprovalDocument(Base):
    __tablename__ = "approval_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    document_number: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    template_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("document_templates.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="DRAFT")  # DRAFT, SUBMITTED, IN_PROGRESS, APPROVED, REJECTED, CANCELLED
    urgency: Mapped[str] = mapped_column(String(10), default="NORMAL")  # LOW, NORMAL, HIGH, URGENT
    submitted_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    submitted_at: Mapped[str | None] = mapped_column(String(30), nullable=True)
    completed_at: Mapped[str | None] = mapped_column(String(30), nullable=True)

    created_at: Mapped[str] = mapped_column(String(30), default=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Mapped[str] = mapped_column(String(30), default=lambda: datetime.now(timezone.utc).isoformat(), onupdate=lambda: datetime.now(timezone.utc).isoformat())
    deleted_at: Mapped[str | None] = mapped_column(String(30), nullable=True)

    template: Mapped["DocumentTemplate | None"] = relationship()
    submitter: Mapped["User"] = relationship("User")
    lines: Mapped[list["ApprovalLine"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    references: Mapped[list["ApprovalReference"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class ApprovalLine(Base):
    __tablename__ = "approval_lines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("approval_documents.id"), nullable=False)
    approver_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    step_order: Mapped[int] = mapped_column(Integer, default=0)
    line_type: Mapped[str] = mapped_column(String(20), default="SEQUENTIAL")  # SEQUENTIAL, PARALLEL, AGREEMENT
    status: Mapped[str] = mapped_column(String(20), default="PENDING")  # PENDING, APPROVED, REJECTED
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    acted_at: Mapped[str | None] = mapped_column(String(30), nullable=True)

    created_at: Mapped[str] = mapped_column(String(30), default=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Mapped[str] = mapped_column(String(30), default=lambda: datetime.now(timezone.utc).isoformat(), onupdate=lambda: datetime.now(timezone.utc).isoformat())

    document: Mapped["ApprovalDocument"] = relationship(back_populates="lines")
    approver: Mapped["User"] = relationship("User")


class ApprovalReference(Base):
    __tablename__ = "approval_references"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("approval_documents.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[str] = mapped_column(String(30), default=lambda: datetime.now(timezone.utc).isoformat())

    document: Mapped["ApprovalDocument"] = relationship(back_populates="references")
    user: Mapped["User"] = relationship("User")


from app.models.user import User  # noqa: E402, F401

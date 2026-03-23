from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    attachable_type: Mapped[str] = mapped_column(String(50), nullable=False)  # notice, post, approval, etc.
    attachable_id: Mapped[str] = mapped_column(String(36), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    thumbnail_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    uploaded_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)

    created_at: Mapped[str] = mapped_column(String(30), default=lambda: datetime.now(timezone.utc).isoformat())
    deleted_at: Mapped[str | None] = mapped_column(String(30), nullable=True)

    uploader: Mapped["User"] = relationship("User")


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    commentable_type: Mapped[str] = mapped_column(String(50), nullable=False)
    commentable_id: Mapped[str] = mapped_column(String(36), nullable=False)
    parent_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("comments.id"), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    author_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)

    created_at: Mapped[str] = mapped_column(String(30), default=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Mapped[str] = mapped_column(String(30), default=lambda: datetime.now(timezone.utc).isoformat(), onupdate=lambda: datetime.now(timezone.utc).isoformat())
    deleted_at: Mapped[str | None] = mapped_column(String(30), nullable=True)

    author: Mapped["User"] = relationship("User")
    parent: Mapped["Comment | None"] = relationship("Comment", remote_side="Comment.id", backref="replies")


from app.models.user import User  # noqa: E402, F401

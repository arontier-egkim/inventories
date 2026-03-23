from pydantic import BaseModel


class AttachmentResponse(BaseModel):
    id: str
    attachable_type: str
    attachable_id: str
    file_name: str
    file_path: str
    file_size: int
    mime_type: str | None = None
    thumbnail_path: str | None = None
    uploaded_by: str
    created_at: str

    model_config = {"from_attributes": True}


class CommentCreate(BaseModel):
    content: str
    parent_id: str | None = None


class CommentUpdate(BaseModel):
    content: str


class CommentResponse(BaseModel):
    id: str
    commentable_type: str
    commentable_id: str
    parent_id: str | None = None
    content: str
    is_deleted: bool
    author_id: str
    author_name: str | None = None
    created_at: str
    updated_at: str
    replies: list["CommentResponse"] = []

    model_config = {"from_attributes": True}

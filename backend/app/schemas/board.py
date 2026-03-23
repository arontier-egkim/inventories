from pydantic import BaseModel


class NoticeCategoryResponse(BaseModel):
    id: str
    name: str
    code: str
    sort_order: int

    model_config = {"from_attributes": True}


class NoticeCreate(BaseModel):
    title: str
    content: str
    category_id: str | None = None
    is_pinned: bool = False
    is_must_read: bool = False


class NoticeResponse(BaseModel):
    id: str
    title: str
    content: str
    category_id: str | None = None
    category_name: str | None = None
    author_id: str
    author_name: str | None = None
    is_pinned: bool
    is_must_read: bool
    view_count: int
    is_read: bool = False
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class NoticeListResponse(BaseModel):
    id: str
    title: str
    category_name: str | None = None
    author_name: str | None = None
    is_pinned: bool
    is_must_read: bool
    view_count: int
    created_at: str

    model_config = {"from_attributes": True}


class BoardResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    type: str
    department_id: str | None = None
    is_active: bool
    created_at: str

    model_config = {"from_attributes": True}


class PostCreate(BaseModel):
    title: str
    content: str
    is_pinned: bool = False


class PostResponse(BaseModel):
    id: str
    board_id: str
    title: str
    content: str
    author_id: str
    author_name: str | None = None
    is_pinned: bool
    view_count: int
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}

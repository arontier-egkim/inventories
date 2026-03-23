from pydantic import BaseModel


class ApprovalLineCreate(BaseModel):
    approver_id: str
    step_order: int = 0
    line_type: str = "SEQUENTIAL"


class ApprovalReferenceCreate(BaseModel):
    user_id: str


class ApprovalCreate(BaseModel):
    template_id: str | None = None
    title: str
    content_json: str | None = None
    urgency: str = "NORMAL"
    lines: list[ApprovalLineCreate] = []
    references: list[ApprovalReferenceCreate] = []


class ApprovalLineResponse(BaseModel):
    id: str
    approver_id: str
    approver_name: str | None = None
    step_order: int
    line_type: str
    status: str
    comment: str | None = None
    acted_at: str | None = None

    model_config = {"from_attributes": True}


class ApprovalReferenceResponse(BaseModel):
    id: str
    user_id: str
    user_name: str | None = None
    is_read: bool

    model_config = {"from_attributes": True}


class ApprovalResponse(BaseModel):
    id: str
    document_number: str | None = None
    template_id: str | None = None
    title: str
    content_json: str | None = None
    status: str
    urgency: str
    submitted_by: str
    submitter_name: str | None = None
    submitted_at: str | None = None
    completed_at: str | None = None
    created_at: str
    updated_at: str
    lines: list[ApprovalLineResponse] = []
    references: list[ApprovalReferenceResponse] = []

    model_config = {"from_attributes": True}


class ApprovalActionRequest(BaseModel):
    comment: str | None = None


class ApprovalDashboardSummary(BaseModel):
    pending_count: int = 0
    approved_count: int = 0
    rejected_count: int = 0
    draft_count: int = 0

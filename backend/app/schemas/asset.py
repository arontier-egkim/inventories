from pydantic import BaseModel


class AssetCategoryResponse(BaseModel):
    id: str
    name: str
    code: str
    parent_id: str | None = None
    level: int
    sort_order: int
    children: list["AssetCategoryResponse"] = []

    model_config = {"from_attributes": True}


class AssetCreate(BaseModel):
    asset_number: str
    category_id: str | None = None
    name: str
    manufacturer: str | None = None
    model: str | None = None
    serial_number: str | None = None
    spec_json: str | None = None
    purchase_date: str | None = None
    purchase_price: float | None = None
    location: str | None = None
    status: str = "AVAILABLE"


class AssetUpdate(BaseModel):
    name: str | None = None
    category_id: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    serial_number: str | None = None
    spec_json: str | None = None
    purchase_date: str | None = None
    purchase_price: float | None = None
    location: str | None = None
    status: str | None = None
    image_url: str | None = None


class AssetResponse(BaseModel):
    id: str
    asset_number: str
    category_id: str | None = None
    category_name: str | None = None
    name: str
    manufacturer: str | None = None
    model: str | None = None
    serial_number: str | None = None
    spec_json: str | None = None
    purchase_date: str | None = None
    purchase_price: float | None = None
    location: str | None = None
    status: str
    image_url: str | None = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class AssetAssignRequest(BaseModel):
    assignee_type: str  # USER, DEPARTMENT
    assignee_id: str


class AssetAssignmentResponse(BaseModel):
    id: str
    asset_id: str
    assignee_type: str
    assignee_id: str
    assigned_by: str
    assigned_at: str
    returned_at: str | None = None
    is_active: bool

    model_config = {"from_attributes": True}


class AssetHistoryResponse(BaseModel):
    id: str
    asset_id: str
    action: str
    from_value: str | None = None
    to_value: str | None = None
    performed_by: str
    performed_at: str
    note: str | None = None

    model_config = {"from_attributes": True}


class AssetReportSummary(BaseModel):
    total: int = 0
    in_use: int = 0
    available: int = 0
    in_repair: int = 0
    disposed: int = 0
    by_category: list[dict] = []

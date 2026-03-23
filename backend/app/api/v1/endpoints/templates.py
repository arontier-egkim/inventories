from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.approval import DocumentTemplate

router = APIRouter(prefix="/templates", tags=["Templates"])


class TemplateCreate:
    pass


from pydantic import BaseModel


class TemplateCreateSchema(BaseModel):
    name: str
    description: str | None = None
    category: str | None = None
    fields_schema_json: str | None = None
    is_active: bool = True
    sort_order: int = 0


class TemplateResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    category: str | None = None
    fields_schema_json: str | None = None
    is_active: bool
    sort_order: int
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


@router.get("", response_model=list[TemplateResponse])
def list_templates(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    templates = db.query(DocumentTemplate).filter(DocumentTemplate.is_active.is_(True)).order_by(DocumentTemplate.sort_order).all()
    return [TemplateResponse.model_validate(t) for t in templates]


@router.post("", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    body: TemplateCreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    template = DocumentTemplate(**body.model_dump())
    db.add(template)
    db.commit()
    db.refresh(template)
    return TemplateResponse.model_validate(template)


@router.get("/{template_id}", response_model=TemplateResponse)
def get_template(template_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    template = db.query(DocumentTemplate).filter(DocumentTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return TemplateResponse.model_validate(template)

import os
import shutil
from uuid import uuid4
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.core.config import settings
from app.models.user import User
from app.models.attachment import Attachment
from app.schemas.attachment import AttachmentResponse

router = APIRouter(prefix="/attachments", tags=["Attachments"])


@router.post("", response_model=AttachmentResponse, status_code=201)
def upload_attachment(
    file: UploadFile = File(...),
    attachable_type: str = Form(...),
    attachable_id: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    upload_dir = os.path.join(settings.UPLOAD_DIR, attachable_type, attachable_id)
    os.makedirs(upload_dir, exist_ok=True)

    file_ext = os.path.splitext(file.filename or "file")[1]
    stored_name = f"{uuid4()}{file_ext}"
    file_path = os.path.join(upload_dir, stored_name)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    file_size = os.path.getsize(file_path)

    attachment = Attachment(
        attachable_type=attachable_type,
        attachable_id=attachable_id,
        file_name=file.filename or "file",
        file_path=file_path,
        file_size=file_size,
        mime_type=file.content_type,
        uploaded_by=current_user.id,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return AttachmentResponse.model_validate(attachment)


@router.get("/{attachment_id}/download")
def download_attachment(
    attachment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attachment = db.query(Attachment).filter(
        Attachment.id == attachment_id,
        Attachment.deleted_at.is_(None),
    ).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    if not os.path.exists(attachment.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        attachment.file_path,
        filename=attachment.file_name,
        media_type=attachment.mime_type or "application/octet-stream",
    )


@router.get("", response_model=list[AttachmentResponse])
def list_attachments(
    attachable_type: str = Query(...),
    attachable_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attachments = db.query(Attachment).filter(
        Attachment.attachable_type == attachable_type,
        Attachment.attachable_id == attachable_id,
        Attachment.deleted_at.is_(None),
    ).all()
    return [AttachmentResponse.model_validate(a) for a in attachments]


@router.delete("/{attachment_id}")
def delete_attachment(
    attachment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attachment = db.query(Attachment).filter(
        Attachment.id == attachment_id,
        Attachment.deleted_at.is_(None),
    ).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    attachment.deleted_at = datetime.now(timezone.utc).isoformat()
    db.commit()
    return {"message": "Attachment deleted"}

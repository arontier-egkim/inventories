from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.approval import ApprovalDocument, ApprovalLine, ApprovalReference
from app.schemas.approval import (
    ApprovalCreate,
    ApprovalResponse,
    ApprovalLineResponse,
    ApprovalReferenceResponse,
    ApprovalActionRequest,
    ApprovalDashboardSummary,
)

router = APIRouter(prefix="/approvals", tags=["Approvals"])


def _build_response(doc: ApprovalDocument, db: Session) -> ApprovalResponse:
    lines = []
    for line in doc.lines:
        approver = db.query(User).filter(User.id == line.approver_id).first()
        lines.append(ApprovalLineResponse(
            id=line.id, approver_id=line.approver_id,
            approver_name=approver.name if approver else None,
            step_order=line.step_order, line_type=line.line_type,
            status=line.status, comment=line.comment, acted_at=line.acted_at,
        ))
    refs = []
    for ref in doc.references:
        ref_user = db.query(User).filter(User.id == ref.user_id).first()
        refs.append(ApprovalReferenceResponse(
            id=ref.id, user_id=ref.user_id,
            user_name=ref_user.name if ref_user else None,
            is_read=ref.is_read,
        ))
    submitter = db.query(User).filter(User.id == doc.submitted_by).first()
    return ApprovalResponse(
        id=doc.id, document_number=doc.document_number, template_id=doc.template_id,
        title=doc.title, content_json=doc.content_json, status=doc.status,
        urgency=doc.urgency, submitted_by=doc.submitted_by,
        submitter_name=submitter.name if submitter else None,
        submitted_at=doc.submitted_at, completed_at=doc.completed_at,
        created_at=doc.created_at, updated_at=doc.updated_at,
        lines=lines, references=refs,
    )


@router.get("", response_model=list[ApprovalResponse])
def list_approvals(
    skip: int = 0, limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    docs = db.query(ApprovalDocument).filter(
        ApprovalDocument.deleted_at.is_(None),
    ).order_by(ApprovalDocument.created_at.desc()).offset(skip).limit(limit).all()
    return [_build_response(d, db) for d in docs]


@router.post("", response_model=ApprovalResponse, status_code=status.HTTP_201_CREATED)
def create_approval(
    body: ApprovalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = db.query(func.count(ApprovalDocument.id)).scalar() or 0
    doc_number = f"DOC-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{count + 1:04d}"

    doc = ApprovalDocument(
        document_number=doc_number,
        template_id=body.template_id,
        title=body.title,
        content_json=body.content_json,
        urgency=body.urgency,
        submitted_by=current_user.id,
    )
    db.add(doc)
    db.flush()

    for line_data in body.lines:
        line = ApprovalLine(
            document_id=doc.id,
            approver_id=line_data.approver_id,
            step_order=line_data.step_order,
            line_type=line_data.line_type,
        )
        db.add(line)

    for ref_data in body.references:
        ref = ApprovalReference(document_id=doc.id, user_id=ref_data.user_id)
        db.add(ref)

    db.commit()
    db.refresh(doc)
    return _build_response(doc, db)


@router.get("/dashboard/summary", response_model=ApprovalDashboardSummary)
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pending = db.query(func.count(ApprovalLine.id)).filter(
        ApprovalLine.approver_id == current_user.id,
        ApprovalLine.status == "PENDING",
    ).scalar() or 0

    submitted_docs = db.query(ApprovalDocument).filter(
        ApprovalDocument.submitted_by == current_user.id,
        ApprovalDocument.deleted_at.is_(None),
    ).all()

    approved = sum(1 for d in submitted_docs if d.status == "APPROVED")
    rejected = sum(1 for d in submitted_docs if d.status == "REJECTED")
    draft = sum(1 for d in submitted_docs if d.status == "DRAFT")

    return ApprovalDashboardSummary(
        pending_count=pending, approved_count=approved,
        rejected_count=rejected, draft_count=draft,
    )


@router.get("/pending", response_model=list[ApprovalResponse])
def list_pending(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pending_lines = db.query(ApprovalLine).filter(
        ApprovalLine.approver_id == current_user.id,
        ApprovalLine.status == "PENDING",
    ).all()
    doc_ids = [line.document_id for line in pending_lines]
    docs = db.query(ApprovalDocument).filter(
        ApprovalDocument.id.in_(doc_ids),
        ApprovalDocument.deleted_at.is_(None),
    ).all()
    return [_build_response(d, db) for d in docs]


@router.get("/drafted", response_model=list[ApprovalResponse])
def list_drafted(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    docs = db.query(ApprovalDocument).filter(
        ApprovalDocument.submitted_by == current_user.id,
        ApprovalDocument.status == "DRAFT",
        ApprovalDocument.deleted_at.is_(None),
    ).all()
    return [_build_response(d, db) for d in docs]


@router.get("/{doc_id}", response_model=ApprovalResponse)
def get_approval(
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(ApprovalDocument).filter(
        ApprovalDocument.id == doc_id,
        ApprovalDocument.deleted_at.is_(None),
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return _build_response(doc, db)


@router.put("/{doc_id}/submit", response_model=ApprovalResponse)
def submit_approval(
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(ApprovalDocument).filter(
        ApprovalDocument.id == doc_id,
        ApprovalDocument.submitted_by == current_user.id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status not in ("DRAFT",):
        raise HTTPException(status_code=400, detail="Can only submit draft documents")

    doc.status = "SUBMITTED"
    doc.submitted_at = datetime.now(timezone.utc).isoformat()
    db.commit()
    db.refresh(doc)
    return _build_response(doc, db)


@router.put("/{doc_id}/approve", response_model=ApprovalResponse)
def approve_document(
    doc_id: str,
    body: ApprovalActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(ApprovalDocument).filter(
        ApprovalDocument.id == doc_id,
        ApprovalDocument.deleted_at.is_(None),
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    line = db.query(ApprovalLine).filter(
        ApprovalLine.document_id == doc_id,
        ApprovalLine.approver_id == current_user.id,
        ApprovalLine.status == "PENDING",
    ).first()
    if not line:
        raise HTTPException(status_code=400, detail="No pending approval line found for you")

    now = datetime.now(timezone.utc).isoformat()
    line.status = "APPROVED"
    line.comment = body.comment
    line.acted_at = now

    all_lines = db.query(ApprovalLine).filter(ApprovalLine.document_id == doc_id).all()
    if all(l.status == "APPROVED" for l in all_lines):
        doc.status = "APPROVED"
        doc.completed_at = now
    else:
        doc.status = "IN_PROGRESS"

    db.commit()
    db.refresh(doc)
    return _build_response(doc, db)


@router.put("/{doc_id}/reject", response_model=ApprovalResponse)
def reject_document(
    doc_id: str,
    body: ApprovalActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(ApprovalDocument).filter(
        ApprovalDocument.id == doc_id,
        ApprovalDocument.deleted_at.is_(None),
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    line = db.query(ApprovalLine).filter(
        ApprovalLine.document_id == doc_id,
        ApprovalLine.approver_id == current_user.id,
        ApprovalLine.status == "PENDING",
    ).first()
    if not line:
        raise HTTPException(status_code=400, detail="No pending approval line found for you")

    now = datetime.now(timezone.utc).isoformat()
    line.status = "REJECTED"
    line.comment = body.comment
    line.acted_at = now
    doc.status = "REJECTED"
    doc.completed_at = now

    db.commit()
    db.refresh(doc)
    return _build_response(doc, db)

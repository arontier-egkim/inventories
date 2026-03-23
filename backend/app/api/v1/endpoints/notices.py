from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.board import Notice, NoticeRead, NoticeCategory
from app.schemas.board import NoticeCreate, NoticeResponse, NoticeListResponse

router = APIRouter(prefix="/notices", tags=["Notices"])


@router.get("", response_model=list[NoticeListResponse])
def list_notices(
    skip: int = 0, limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notices = db.query(Notice).filter(Notice.deleted_at.is_(None)).order_by(
        Notice.is_pinned.desc(), Notice.created_at.desc()
    ).offset(skip).limit(limit).all()

    result = []
    for n in notices:
        result.append(NoticeListResponse(
            id=n.id, title=n.title,
            category_name=n.category.name if n.category else None,
            author_name=n.author.name if n.author else None,
            is_pinned=n.is_pinned, is_must_read=n.is_must_read,
            view_count=n.view_count, created_at=n.created_at,
        ))
    return result


@router.post("", response_model=NoticeResponse, status_code=status.HTTP_201_CREATED)
def create_notice(
    body: NoticeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notice = Notice(
        title=body.title, content=body.content,
        category_id=body.category_id, author_id=current_user.id,
        is_pinned=body.is_pinned, is_must_read=body.is_must_read,
    )
    db.add(notice)
    db.commit()
    db.refresh(notice)
    return NoticeResponse(
        id=notice.id, title=notice.title, content=notice.content,
        category_id=notice.category_id,
        category_name=notice.category.name if notice.category else None,
        author_id=notice.author_id, author_name=current_user.name,
        is_pinned=notice.is_pinned, is_must_read=notice.is_must_read,
        view_count=notice.view_count, created_at=notice.created_at,
        updated_at=notice.updated_at,
    )


@router.get("/{notice_id}", response_model=NoticeResponse)
def get_notice(
    notice_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notice = db.query(Notice).filter(Notice.id == notice_id, Notice.deleted_at.is_(None)).first()
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")

    notice.view_count += 1
    db.commit()

    is_read = db.query(NoticeRead).filter(
        NoticeRead.notice_id == notice_id,
        NoticeRead.user_id == current_user.id,
    ).first() is not None

    return NoticeResponse(
        id=notice.id, title=notice.title, content=notice.content,
        category_id=notice.category_id,
        category_name=notice.category.name if notice.category else None,
        author_id=notice.author_id,
        author_name=notice.author.name if notice.author else None,
        is_pinned=notice.is_pinned, is_must_read=notice.is_must_read,
        view_count=notice.view_count, is_read=is_read,
        created_at=notice.created_at, updated_at=notice.updated_at,
    )


@router.post("/{notice_id}/read")
def mark_notice_read(
    notice_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notice = db.query(Notice).filter(Notice.id == notice_id).first()
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")

    existing = db.query(NoticeRead).filter(
        NoticeRead.notice_id == notice_id,
        NoticeRead.user_id == current_user.id,
    ).first()

    if not existing:
        nr = NoticeRead(notice_id=notice_id, user_id=current_user.id)
        db.add(nr)
        db.commit()

    return {"message": "Marked as read"}

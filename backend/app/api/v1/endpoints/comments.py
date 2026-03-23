from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.attachment import Comment
from app.schemas.attachment import CommentCreate, CommentUpdate, CommentResponse

router = APIRouter(tags=["Comments"])


def _build_comment(c: Comment) -> CommentResponse:
    replies = []
    if hasattr(c, "replies") and c.replies:
        replies = [_build_comment(r) for r in c.replies if not r.is_deleted]
    return CommentResponse(
        id=c.id, commentable_type=c.commentable_type, commentable_id=c.commentable_id,
        parent_id=c.parent_id, content=c.content if not c.is_deleted else "[deleted]",
        is_deleted=c.is_deleted, author_id=c.author_id,
        author_name=c.author.name if c.author else None,
        created_at=c.created_at, updated_at=c.updated_at,
        replies=replies,
    )


@router.get("/{resource_type}/{resource_id}/comments", response_model=list[CommentResponse])
def list_comments(
    resource_type: str, resource_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comments = db.query(Comment).filter(
        Comment.commentable_type == resource_type,
        Comment.commentable_id == resource_id,
        Comment.parent_id.is_(None),
        Comment.deleted_at.is_(None),
    ).order_by(Comment.created_at).all()
    return [_build_comment(c) for c in comments]


@router.post("/{resource_type}/{resource_id}/comments", response_model=CommentResponse, status_code=201)
def create_comment(
    resource_type: str, resource_id: str,
    body: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment = Comment(
        commentable_type=resource_type,
        commentable_id=resource_id,
        parent_id=body.parent_id,
        content=body.content,
        author_id=current_user.id,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return _build_comment(comment)


@router.put("/{resource_type}/{resource_id}/comments/{comment_id}", response_model=CommentResponse)
def update_comment(
    resource_type: str, resource_id: str, comment_id: str,
    body: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment = db.query(Comment).filter(
        Comment.id == comment_id,
        Comment.author_id == current_user.id,
    ).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    comment.content = body.content
    db.commit()
    db.refresh(comment)
    return _build_comment(comment)


@router.delete("/{resource_type}/{resource_id}/comments/{comment_id}")
def delete_comment(
    resource_type: str, resource_id: str, comment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment = db.query(Comment).filter(
        Comment.id == comment_id,
        Comment.author_id == current_user.id,
    ).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    comment.is_deleted = True
    comment.deleted_at = datetime.now(timezone.utc).isoformat()
    db.commit()
    return {"message": "Comment deleted"}

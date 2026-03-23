from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.board import Board, Post
from app.schemas.board import BoardResponse, PostCreate, PostResponse

router = APIRouter(prefix="/boards", tags=["Boards"])


@router.get("", response_model=list[BoardResponse])
def list_boards(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    boards = db.query(Board).filter(Board.is_active.is_(True)).all()
    return [BoardResponse.model_validate(b) for b in boards]


@router.get("/{board_id}/posts", response_model=list[PostResponse])
def list_posts(
    board_id: str,
    skip: int = 0, limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")

    posts = db.query(Post).filter(
        Post.board_id == board_id,
        Post.deleted_at.is_(None),
    ).order_by(Post.is_pinned.desc(), Post.created_at.desc()).offset(skip).limit(limit).all()

    return [PostResponse(
        id=p.id, board_id=p.board_id, title=p.title, content=p.content,
        author_id=p.author_id, author_name=p.author.name if p.author else None,
        is_pinned=p.is_pinned, view_count=p.view_count,
        created_at=p.created_at, updated_at=p.updated_at,
    ) for p in posts]


@router.post("/{board_id}/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(
    board_id: str,
    body: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")

    post = Post(
        board_id=board_id, title=body.title, content=body.content,
        author_id=current_user.id, is_pinned=body.is_pinned,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return PostResponse(
        id=post.id, board_id=post.board_id, title=post.title, content=post.content,
        author_id=post.author_id, author_name=current_user.name,
        is_pinned=post.is_pinned, view_count=post.view_count,
        created_at=post.created_at, updated_at=post.updated_at,
    )


@router.get("/{board_id}/posts/{post_id}", response_model=PostResponse)
def get_post(
    board_id: str, post_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.query(Post).filter(
        Post.id == post_id, Post.board_id == board_id, Post.deleted_at.is_(None),
    ).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    post.view_count += 1
    db.commit()

    return PostResponse(
        id=post.id, board_id=post.board_id, title=post.title, content=post.content,
        author_id=post.author_id, author_name=post.author.name if post.author else None,
        is_pinned=post.is_pinned, view_count=post.view_count,
        created_at=post.created_at, updated_at=post.updated_at,
    )

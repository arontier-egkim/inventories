from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.attendance import AttendanceRecord
from app.schemas.attendance import CheckInRequest, CheckOutRequest, AttendanceResponse

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.post("/check-in", response_model=AttendanceResponse)
def check_in(
    body: CheckInRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    existing = db.query(AttendanceRecord).filter(
        AttendanceRecord.user_id == current_user.id,
        AttendanceRecord.date == today,
    ).first()

    if existing and existing.check_in_at:
        raise HTTPException(status_code=400, detail="Already checked in today")

    now = datetime.now(timezone.utc).isoformat()

    if existing:
        existing.check_in_at = now
        existing.note = body.note
        db.commit()
        db.refresh(existing)
        return AttendanceResponse.model_validate(existing)

    # Determine if late (after 09:00 UTC — simplified)
    hour = datetime.now(timezone.utc).hour
    status = "LATE" if hour >= 9 else "NORMAL"

    record = AttendanceRecord(
        user_id=current_user.id,
        date=today,
        check_in_at=now,
        status=status,
        note=body.note,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return AttendanceResponse.model_validate(record)


@router.post("/check-out", response_model=AttendanceResponse)
def check_out(
    body: CheckOutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    record = db.query(AttendanceRecord).filter(
        AttendanceRecord.user_id == current_user.id,
        AttendanceRecord.date == today,
    ).first()

    if not record or not record.check_in_at:
        raise HTTPException(status_code=400, detail="Must check in first")

    if record.check_out_at:
        raise HTTPException(status_code=400, detail="Already checked out today")

    now = datetime.now(timezone.utc)
    record.check_out_at = now.isoformat()

    # Calculate work minutes
    try:
        check_in_time = datetime.fromisoformat(record.check_in_at)
        delta = now - check_in_time
        record.work_minutes = int(delta.total_seconds() / 60)
    except Exception:
        record.work_minutes = 0

    if body.note:
        record.note = body.note

    db.commit()
    db.refresh(record)
    return AttendanceResponse.model_validate(record)


@router.get("/today", response_model=AttendanceResponse | None)
def get_today(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    record = db.query(AttendanceRecord).filter(
        AttendanceRecord.user_id == current_user.id,
        AttendanceRecord.date == today,
    ).first()
    if not record:
        return None
    return AttendanceResponse.model_validate(record)


@router.get("/monthly", response_model=list[AttendanceResponse])
def get_monthly(
    year: int = Query(...),
    month: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prefix = f"{year}-{month:02d}"
    records = db.query(AttendanceRecord).filter(
        AttendanceRecord.user_id == current_user.id,
        AttendanceRecord.date.startswith(prefix),
    ).order_by(AttendanceRecord.date).all()
    return [AttendanceResponse.model_validate(r) for r in records]

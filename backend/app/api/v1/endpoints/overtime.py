from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.overtime import OvertimeRequest, WeeklyWorkSummary
from app.schemas.overtime import OvertimeRequestCreate, OvertimeRequestResponse, WeeklyWorkSummaryResponse

router = APIRouter(prefix="/overtime", tags=["Overtime"])


@router.post("/requests", response_model=OvertimeRequestResponse, status_code=status.HTTP_201_CREATED)
def create_overtime_request(
    body: OvertimeRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    request = OvertimeRequest(
        user_id=current_user.id,
        date=body.date,
        type=body.type,
        planned_start=body.planned_start,
        planned_end=body.planned_end,
        planned_hours=body.planned_hours,
        reason=body.reason,
    )
    db.add(request)
    db.commit()
    db.refresh(request)

    return OvertimeRequestResponse(
        id=request.id, user_id=request.user_id, user_name=current_user.name,
        date=request.date, type=request.type,
        planned_start=request.planned_start, planned_end=request.planned_end,
        planned_hours=request.planned_hours, reason=request.reason,
        status=request.status, approver_id=request.approver_id,
        created_at=request.created_at,
    )


@router.get("/requests", response_model=list[OvertimeRequestResponse])
def list_overtime_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    requests = db.query(OvertimeRequest).filter(
        OvertimeRequest.user_id == current_user.id,
    ).order_by(OvertimeRequest.created_at.desc()).all()

    result = []
    for r in requests:
        result.append(OvertimeRequestResponse(
            id=r.id, user_id=r.user_id,
            user_name=r.user.name if r.user else None,
            date=r.date, type=r.type,
            planned_start=r.planned_start, planned_end=r.planned_end,
            planned_hours=r.planned_hours, reason=r.reason,
            status=r.status, approver_id=r.approver_id,
            approver_name=r.approver.name if r.approver else None,
            created_at=r.created_at,
        ))
    return result


@router.get("/weekly-summary", response_model=list[WeeklyWorkSummaryResponse])
def get_weekly_summary(
    year: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if year is None:
        year = datetime.now(timezone.utc).year

    summaries = db.query(WeeklyWorkSummary).filter(
        WeeklyWorkSummary.user_id == current_user.id,
        WeeklyWorkSummary.year == year,
    ).order_by(WeeklyWorkSummary.week_number).all()
    return [WeeklyWorkSummaryResponse.model_validate(s) for s in summaries]


@router.post("/requests/{request_id}/approve")
def approve_overtime(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ot_req = db.query(OvertimeRequest).filter(OvertimeRequest.id == request_id).first()
    if not ot_req:
        raise HTTPException(status_code=404, detail="Overtime request not found")
    if ot_req.status != "PENDING":
        raise HTTPException(status_code=400, detail="Request is not pending")

    ot_req.status = "APPROVED"
    ot_req.approver_id = current_user.id
    db.commit()
    return {"message": "Overtime request approved"}

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.leave import LeaveType, LeaveBalance, LeaveRequest
from app.schemas.leave import LeaveBalanceResponse, LeaveRequestCreate, LeaveRequestResponse

router = APIRouter(prefix="/leaves", tags=["Leaves"])


@router.get("/balance", response_model=list[LeaveBalanceResponse])
def get_balance(
    year: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if year is None:
        year = datetime.now(timezone.utc).year

    balances = db.query(LeaveBalance).filter(
        LeaveBalance.user_id == current_user.id,
        LeaveBalance.year == year,
    ).all()

    result = []
    for b in balances:
        result.append(LeaveBalanceResponse(
            id=b.id, user_id=b.user_id, leave_type_id=b.leave_type_id,
            leave_type_name=b.leave_type.name if b.leave_type else None,
            year=b.year, total_days=b.total_days, used_days=b.used_days,
            remaining_days=b.total_days - b.used_days,
        ))
    return result


@router.post("/requests", response_model=LeaveRequestResponse, status_code=status.HTTP_201_CREATED)
def create_leave_request(
    body: LeaveRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    leave_type = db.query(LeaveType).filter(LeaveType.id == body.leave_type_id).first()
    if not leave_type:
        raise HTTPException(status_code=404, detail="Leave type not found")

    request = LeaveRequest(
        user_id=current_user.id,
        leave_type_id=body.leave_type_id,
        start_date=body.start_date,
        end_date=body.end_date,
        days=body.days,
        reason=body.reason,
    )
    db.add(request)
    db.commit()
    db.refresh(request)

    return LeaveRequestResponse(
        id=request.id, user_id=request.user_id, user_name=current_user.name,
        leave_type_id=request.leave_type_id, leave_type_name=leave_type.name,
        start_date=request.start_date, end_date=request.end_date,
        days=request.days, reason=request.reason, status=request.status,
        approver_id=request.approver_id, created_at=request.created_at,
    )


@router.get("/requests", response_model=list[LeaveRequestResponse])
def list_leave_requests(
    status_filter: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(LeaveRequest).filter(LeaveRequest.user_id == current_user.id)
    if status_filter:
        query = query.filter(LeaveRequest.status == status_filter)
    requests = query.order_by(LeaveRequest.created_at.desc()).all()

    result = []
    for r in requests:
        result.append(LeaveRequestResponse(
            id=r.id, user_id=r.user_id,
            user_name=r.user.name if r.user else None,
            leave_type_id=r.leave_type_id,
            leave_type_name=r.leave_type.name if r.leave_type else None,
            start_date=r.start_date, end_date=r.end_date,
            days=r.days, reason=r.reason, status=r.status,
            approver_id=r.approver_id,
            approver_name=r.approver.name if r.approver else None,
            created_at=r.created_at,
        ))
    return result


@router.post("/requests/{request_id}/approve")
def approve_leave(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    leave_req = db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()
    if not leave_req:
        raise HTTPException(status_code=404, detail="Leave request not found")
    if leave_req.status != "PENDING":
        raise HTTPException(status_code=400, detail="Request is not pending")

    leave_req.status = "APPROVED"
    leave_req.approver_id = current_user.id

    # Update balance
    year = int(leave_req.start_date[:4])
    balance = db.query(LeaveBalance).filter(
        LeaveBalance.user_id == leave_req.user_id,
        LeaveBalance.leave_type_id == leave_req.leave_type_id,
        LeaveBalance.year == year,
    ).first()
    if balance:
        balance.used_days += leave_req.days

    db.commit()
    return {"message": "Leave request approved"}


@router.post("/requests/{request_id}/reject")
def reject_leave(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    leave_req = db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()
    if not leave_req:
        raise HTTPException(status_code=404, detail="Leave request not found")
    if leave_req.status != "PENDING":
        raise HTTPException(status_code=400, detail="Request is not pending")

    leave_req.status = "REJECTED"
    leave_req.approver_id = current_user.id
    db.commit()
    return {"message": "Leave request rejected"}

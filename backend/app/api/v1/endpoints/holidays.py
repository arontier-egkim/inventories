from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.attendance import Holiday
from app.schemas.attendance import HolidayCreate, HolidayResponse

router = APIRouter(prefix="/holidays", tags=["Holidays"])


@router.get("", response_model=list[HolidayResponse])
def list_holidays(
    year: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Holiday)
    if year:
        query = query.filter(Holiday.year == year)
    holidays = query.order_by(Holiday.date).all()
    return [HolidayResponse.model_validate(h) for h in holidays]


@router.post("", response_model=HolidayResponse, status_code=status.HTTP_201_CREATED)
def create_holiday(
    body: HolidayCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    holiday = Holiday(date=body.date, name=body.name, type=body.type, year=body.year)
    db.add(holiday)
    db.commit()
    db.refresh(holiday)
    return HolidayResponse.model_validate(holiday)

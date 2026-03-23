from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.asset import Asset, AssetCategory, AssetHistory, AssetAssignment
from app.schemas.asset import (
    AssetCreate, AssetUpdate, AssetResponse,
    AssetCategoryResponse, AssetAssignRequest, AssetAssignmentResponse,
    AssetHistoryResponse, AssetReportSummary,
)

router = APIRouter(tags=["Assets"])


def _build_category_tree(categories: list[AssetCategory], parent_id: str | None = None) -> list[AssetCategoryResponse]:
    result = []
    for cat in categories:
        if cat.parent_id == parent_id:
            children = _build_category_tree(categories, cat.id)
            result.append(AssetCategoryResponse(
                id=cat.id, name=cat.name, code=cat.code,
                parent_id=cat.parent_id, level=cat.level,
                sort_order=cat.sort_order, children=children,
            ))
    result.sort(key=lambda x: x.sort_order)
    return result


@router.get("/asset-categories", response_model=list[AssetCategoryResponse])
def list_asset_categories(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    categories = db.query(AssetCategory).all()
    return _build_category_tree(categories, None)


@router.get("/assets", response_model=list[AssetResponse])
def list_assets(
    status_filter: str | None = Query(None, alias="status"),
    category_id: str | None = None,
    skip: int = 0, limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Asset).filter(Asset.deleted_at.is_(None))
    if status_filter:
        query = query.filter(Asset.status == status_filter)
    if category_id:
        query = query.filter(Asset.category_id == category_id)
    assets = query.offset(skip).limit(limit).all()

    return [AssetResponse(
        id=a.id, asset_number=a.asset_number, category_id=a.category_id,
        category_name=a.category.name if a.category else None,
        name=a.name, manufacturer=a.manufacturer, model=a.model,
        serial_number=a.serial_number, spec_json=a.spec_json,
        purchase_date=a.purchase_date, purchase_price=a.purchase_price,
        location=a.location, status=a.status, image_url=a.image_url,
        created_at=a.created_at, updated_at=a.updated_at,
    ) for a in assets]


@router.post("/assets", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
def create_asset(
    body: AssetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    asset = Asset(**body.model_dump())
    db.add(asset)
    db.flush()

    history = AssetHistory(
        asset_id=asset.id, action="CREATED",
        to_value=asset.status, performed_by=current_user.id,
    )
    db.add(history)
    db.commit()
    db.refresh(asset)

    return AssetResponse(
        id=asset.id, asset_number=asset.asset_number, category_id=asset.category_id,
        category_name=asset.category.name if asset.category else None,
        name=asset.name, manufacturer=asset.manufacturer, model=asset.model,
        serial_number=asset.serial_number, spec_json=asset.spec_json,
        purchase_date=asset.purchase_date, purchase_price=asset.purchase_price,
        location=asset.location, status=asset.status, image_url=asset.image_url,
        created_at=asset.created_at, updated_at=asset.updated_at,
    )


@router.get("/assets/report/summary", response_model=AssetReportSummary)
def asset_report_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total = db.query(func.count(Asset.id)).filter(Asset.deleted_at.is_(None)).scalar() or 0
    in_use = db.query(func.count(Asset.id)).filter(Asset.status == "IN_USE", Asset.deleted_at.is_(None)).scalar() or 0
    available = db.query(func.count(Asset.id)).filter(Asset.status == "AVAILABLE", Asset.deleted_at.is_(None)).scalar() or 0
    in_repair = db.query(func.count(Asset.id)).filter(Asset.status == "IN_REPAIR", Asset.deleted_at.is_(None)).scalar() or 0
    disposed = db.query(func.count(Asset.id)).filter(Asset.status == "DISPOSED", Asset.deleted_at.is_(None)).scalar() or 0

    by_category = []
    cats = db.query(AssetCategory).all()
    for cat in cats:
        count = db.query(func.count(Asset.id)).filter(
            Asset.category_id == cat.id, Asset.deleted_at.is_(None)
        ).scalar() or 0
        if count > 0:
            by_category.append({"category": cat.name, "count": count})

    return AssetReportSummary(
        total=total, in_use=in_use, available=available,
        in_repair=in_repair, disposed=disposed, by_category=by_category,
    )


@router.get("/assets/{asset_id}", response_model=AssetResponse)
def get_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.deleted_at.is_(None)).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    return AssetResponse(
        id=asset.id, asset_number=asset.asset_number, category_id=asset.category_id,
        category_name=asset.category.name if asset.category else None,
        name=asset.name, manufacturer=asset.manufacturer, model=asset.model,
        serial_number=asset.serial_number, spec_json=asset.spec_json,
        purchase_date=asset.purchase_date, purchase_price=asset.purchase_price,
        location=asset.location, status=asset.status, image_url=asset.image_url,
        created_at=asset.created_at, updated_at=asset.updated_at,
    )


@router.put("/assets/{asset_id}", response_model=AssetResponse)
def update_asset(
    asset_id: str,
    body: AssetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.deleted_at.is_(None)).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    old_status = asset.status
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(asset, key, value)

    if "status" in update_data and update_data["status"] != old_status:
        history = AssetHistory(
            asset_id=asset.id, action="STATUS_CHANGE",
            from_value=old_status, to_value=update_data["status"],
            performed_by=current_user.id,
        )
        db.add(history)

    db.commit()
    db.refresh(asset)

    return AssetResponse(
        id=asset.id, asset_number=asset.asset_number, category_id=asset.category_id,
        category_name=asset.category.name if asset.category else None,
        name=asset.name, manufacturer=asset.manufacturer, model=asset.model,
        serial_number=asset.serial_number, spec_json=asset.spec_json,
        purchase_date=asset.purchase_date, purchase_price=asset.purchase_price,
        location=asset.location, status=asset.status, image_url=asset.image_url,
        created_at=asset.created_at, updated_at=asset.updated_at,
    )


@router.post("/assets/{asset_id}/assign", response_model=AssetAssignmentResponse)
def assign_asset(
    asset_id: str,
    body: AssetAssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.deleted_at.is_(None)).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Deactivate existing active assignments
    existing = db.query(AssetAssignment).filter(
        AssetAssignment.asset_id == asset_id,
        AssetAssignment.is_active.is_(True),
    ).all()
    now = datetime.now(timezone.utc).isoformat()
    for e in existing:
        e.is_active = False
        e.returned_at = now

    assignment = AssetAssignment(
        asset_id=asset_id,
        assignee_type=body.assignee_type,
        assignee_id=body.assignee_id,
        assigned_by=current_user.id,
    )
    db.add(assignment)

    asset.status = "IN_USE"

    history = AssetHistory(
        asset_id=asset_id, action="ASSIGNED",
        to_value=f"{body.assignee_type}:{body.assignee_id}",
        performed_by=current_user.id,
    )
    db.add(history)

    db.commit()
    db.refresh(assignment)
    return AssetAssignmentResponse.model_validate(assignment)


@router.post("/assets/{asset_id}/return")
def return_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.deleted_at.is_(None)).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    active = db.query(AssetAssignment).filter(
        AssetAssignment.asset_id == asset_id,
        AssetAssignment.is_active.is_(True),
    ).first()

    if not active:
        raise HTTPException(status_code=400, detail="Asset is not currently assigned")

    now = datetime.now(timezone.utc).isoformat()
    active.is_active = False
    active.returned_at = now
    asset.status = "AVAILABLE"

    history = AssetHistory(
        asset_id=asset_id, action="RETURNED",
        from_value=f"{active.assignee_type}:{active.assignee_id}",
        performed_by=current_user.id,
    )
    db.add(history)

    db.commit()
    return {"message": "Asset returned"}

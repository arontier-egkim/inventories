from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.organization import Department, Position, Title, UserDepartment
from app.schemas.organization import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    PositionResponse,
    TitleResponse,
    UserDepartmentAssign,
    OrgChartNode,
)

router = APIRouter(tags=["Organizations"])


def _build_dept_tree(departments: list[Department], parent_id: str | None = None) -> list[DepartmentResponse]:
    result = []
    for dept in departments:
        if dept.parent_id == parent_id:
            children = _build_dept_tree(departments, dept.id)
            result.append(DepartmentResponse(
                id=dept.id,
                name=dept.name,
                code=dept.code,
                parent_id=dept.parent_id,
                level=dept.level,
                sort_order=dept.sort_order,
                is_active=dept.is_active,
                created_at=dept.created_at,
                updated_at=dept.updated_at,
                children=children,
            ))
    result.sort(key=lambda x: x.sort_order)
    return result


@router.get("/departments", response_model=list[DepartmentResponse])
def list_departments(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    departments = db.query(Department).filter(Department.deleted_at.is_(None)).all()
    return _build_dept_tree(departments, None)


@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    body: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dept = Department(**body.model_dump())
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return DepartmentResponse(
        id=dept.id, name=dept.name, code=dept.code, parent_id=dept.parent_id,
        level=dept.level, sort_order=dept.sort_order, is_active=dept.is_active,
        created_at=dept.created_at, updated_at=dept.updated_at, children=[],
    )


@router.get("/departments/{dept_id}", response_model=DepartmentResponse)
def get_department(dept_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    dept = db.query(Department).filter(Department.id == dept_id, Department.deleted_at.is_(None)).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    all_depts = db.query(Department).filter(Department.deleted_at.is_(None)).all()
    children = _build_dept_tree(all_depts, dept.id)
    return DepartmentResponse(
        id=dept.id, name=dept.name, code=dept.code, parent_id=dept.parent_id,
        level=dept.level, sort_order=dept.sort_order, is_active=dept.is_active,
        created_at=dept.created_at, updated_at=dept.updated_at, children=children,
    )


@router.put("/departments/{dept_id}", response_model=DepartmentResponse)
def update_department(
    dept_id: str,
    body: DepartmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dept = db.query(Department).filter(Department.id == dept_id, Department.deleted_at.is_(None)).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(dept, key, value)
    db.commit()
    db.refresh(dept)
    return DepartmentResponse(
        id=dept.id, name=dept.name, code=dept.code, parent_id=dept.parent_id,
        level=dept.level, sort_order=dept.sort_order, is_active=dept.is_active,
        created_at=dept.created_at, updated_at=dept.updated_at, children=[],
    )


@router.delete("/departments/{dept_id}")
def delete_department(dept_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    dept = db.query(Department).filter(Department.id == dept_id, Department.deleted_at.is_(None)).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    from datetime import datetime, timezone
    dept.deleted_at = datetime.now(timezone.utc).isoformat()
    db.commit()
    return {"message": "Department deleted"}


@router.get("/positions", response_model=list[PositionResponse])
def list_positions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    positions = db.query(Position).order_by(Position.sort_order).all()
    return [PositionResponse.model_validate(p) for p in positions]


@router.get("/titles", response_model=list[TitleResponse])
def list_titles(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    titles = db.query(Title).order_by(Title.sort_order).all()
    return [TitleResponse.model_validate(t) for t in titles]


@router.get("/org-chart")
def get_org_chart(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    departments = db.query(Department).filter(Department.deleted_at.is_(None), Department.is_active.is_(True)).all()
    user_depts = db.query(UserDepartment).all()

    dept_members: dict[str, list] = {}
    for ud in user_depts:
        if ud.department_id not in dept_members:
            dept_members[ud.department_id] = []
        dept_members[ud.department_id].append({
            "user_id": ud.user_id,
            "user_name": ud.user.name if ud.user else "",
            "position": ud.position.name if ud.position else None,
            "title": ud.title.name if ud.title else None,
            "is_primary": ud.is_primary,
        })

    def build_chart(parent_id: str | None) -> list[dict]:
        result = []
        for dept in sorted(departments, key=lambda d: d.sort_order):
            if dept.parent_id == parent_id:
                result.append({
                    "department": {
                        "id": dept.id, "name": dept.name, "code": dept.code,
                        "level": dept.level, "sort_order": dept.sort_order,
                    },
                    "members": dept_members.get(dept.id, []),
                    "children": build_chart(dept.id),
                })
        return result

    return build_chart(None)


@router.post("/users/{user_id}/departments")
def assign_user_department(
    user_id: str,
    body: UserDepartmentAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if body.is_primary:
        existing_primary = db.query(UserDepartment).filter(
            UserDepartment.user_id == user_id, UserDepartment.is_primary.is_(True)
        ).all()
        for ep in existing_primary:
            ep.is_primary = False

    ud = UserDepartment(
        user_id=user_id,
        department_id=body.department_id,
        position_id=body.position_id,
        title_id=body.title_id,
        is_primary=body.is_primary,
        start_date=body.start_date,
    )
    db.add(ud)
    db.commit()
    return {"message": "Department assigned"}

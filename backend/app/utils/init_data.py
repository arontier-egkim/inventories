import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.database import engine, Base, SessionLocal
from app.core.security import hash_password

# Import all models so they are registered with Base.metadata
from app.models.user import User, RefreshToken
from app.models.organization import Department, Position, Title, UserDepartment
from app.models.role import Role, Permission, RolePermission, UserRole
from app.models.approval import DocumentTemplate, ApprovalDocument, ApprovalLine, ApprovalReference
from app.models.board import NoticeCategory, Notice, NoticeRead, Board, Post
from app.models.attachment import Attachment, Comment
from app.models.attendance import AttendanceRecord, WorkSchedule, Holiday
from app.models.leave import LeaveType, LeaveBalance, LeaveRequest
from app.models.overtime import OvertimeRequest, OvertimePolicy, WeeklyWorkSummary
from app.models.asset import AssetCategory, Asset, AssetHistory, AssetAssignment


def init_db():
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        # Check if already seeded
        if db.query(User).first():
            return

        now = datetime.now(timezone.utc).isoformat()

        # === 1. Positions ===
        positions_data = [
            ("사원", 1), ("대리", 2), ("과장", 3), ("차장", 4), ("부장", 5),
            ("이사", 6), ("상무", 7), ("전무", 8), ("부사장", 9), ("사장", 10),
        ]
        positions = {}
        for i, (name, level) in enumerate(positions_data):
            p = Position(name=name, level=level, sort_order=i + 1)
            db.add(p)
            db.flush()
            positions[name] = p

        # === 2. Titles ===
        titles_data = [
            ("팀원", 1), ("파트장", 2), ("팀장", 3), ("실장", 4), ("본부장", 5), ("대표이사", 6),
        ]
        titles = {}
        for i, (name, level) in enumerate(titles_data):
            t = Title(name=name, level=level, sort_order=i + 1)
            db.add(t)
            db.flush()
            titles[name] = t

        # === 3. Departments ===
        root = Department(name="아론티어", code="ARONTIER", parent_id=None, level=0, sort_order=1)
        db.add(root)
        db.flush()

        mgmt_div = Department(name="경영지원본부", code="MGMT", parent_id=root.id, level=1, sort_order=1)
        tech_div = Department(name="기술본부", code="TECH", parent_id=root.id, level=1, sort_order=2)
        db.add_all([mgmt_div, tech_div])
        db.flush()

        hr_team = Department(name="인사팀", code="HR", parent_id=mgmt_div.id, level=2, sort_order=1)
        ga_team = Department(name="총무팀", code="GA", parent_id=mgmt_div.id, level=2, sort_order=2)
        dev_team = Department(name="개발팀", code="DEV", parent_id=tech_div.id, level=2, sort_order=1)
        infra_team = Department(name="인프라팀", code="INFRA", parent_id=tech_div.id, level=2, sort_order=2)
        db.add_all([hr_team, ga_team, dev_team, infra_team])
        db.flush()

        depts = {
            "아론티어": root, "경영지원본부": mgmt_div, "기술본부": tech_div,
            "인사팀": hr_team, "총무팀": ga_team, "개발팀": dev_team, "인프라팀": infra_team,
        }

        # === 4. Roles ===
        roles_data = [
            ("시스템 관리자", "SYSTEM_ADMIN", "시스템 전체 관리 권한", True),
            ("부서 관리자", "DEPT_ADMIN", "부서 관리 권한", True),
            ("일반 사용자", "USER", "일반 사용자 권한", True),
        ]
        roles = {}
        for name, code, desc, is_system in roles_data:
            r = Role(name=name, code=code, description=desc, is_system=is_system)
            db.add(r)
            db.flush()
            roles[code] = r

        # === 5. Admin user ===
        admin = User(
            email="admin@arontier.co",
            password_hash=hash_password("admin1234!"),
            name="관리자",
            employee_number="EMP-0001",
            phone="010-0000-0000",
            hire_date="2020-01-01",
            status="ACTIVE",
            is_active=True,
        )
        db.add(admin)
        db.flush()

        # Admin -> 개발팀, 팀장/부장
        admin_dept = UserDepartment(
            user_id=admin.id, department_id=dev_team.id,
            position_id=positions["부장"].id, title_id=titles["팀장"].id,
            is_primary=True, start_date="2020-01-01",
        )
        db.add(admin_dept)

        # Admin -> SYSTEM_ADMIN role
        db.add(UserRole(user_id=admin.id, role_id=roles["SYSTEM_ADMIN"].id))

        # === 6. Sample users ===
        sample_users = [
            ("김개발", "dev.kim@arontier.co", "EMP-0002", "010-1111-1111", "2021-03-01", "개발팀", "과장", "파트장"),
            ("박디자인", "design.park@arontier.co", "EMP-0003", "010-2222-2222", "2021-06-01", "개발팀", "대리", "팀원"),
            ("이영업", "sales.lee@arontier.co", "EMP-0004", "010-3333-3333", "2022-01-01", "경영지원본부", "차장", "본부장"),
            ("정인사", "hr.jung@arontier.co", "EMP-0005", "010-4444-4444", "2022-03-01", "인사팀", "과장", "팀장"),
            ("최총무", "ga.choi@arontier.co", "EMP-0006", "010-5555-5555", "2023-01-01", "총무팀", "대리", "팀원"),
            ("한인프라", "infra.han@arontier.co", "EMP-0007", "010-6666-6666", "2023-06-01", "인프라팀", "사원", "팀원"),
        ]

        for name, email, emp_num, phone, hire_date, dept_name, pos_name, title_name in sample_users:
            u = User(
                email=email,
                password_hash=hash_password("password123!"),
                name=name,
                employee_number=emp_num,
                phone=phone,
                hire_date=hire_date,
                status="ACTIVE",
                is_active=True,
            )
            db.add(u)
            db.flush()

            ud = UserDepartment(
                user_id=u.id, department_id=depts[dept_name].id,
                position_id=positions[pos_name].id, title_id=titles[title_name].id,
                is_primary=True, start_date=hire_date,
            )
            db.add(ud)

            db.add(UserRole(user_id=u.id, role_id=roles["USER"].id))

        # === 7. Leave Types ===
        leave_types = [
            ("연차", "ANNUAL", True, True, 1.0, 15.0, "연차휴가"),
            ("오전반차", "AM_HALF", True, True, 0.5, 0.0, "오전 반차"),
            ("오후반차", "PM_HALF", True, True, 0.5, 0.0, "오후 반차"),
            ("특별휴가", "SPECIAL", True, False, 1.0, 0.0, "경조사 등 특별휴가"),
            ("공가", "PUBLIC", True, False, 1.0, 0.0, "공적 사유 휴가"),
            ("병가", "SICK", True, False, 1.0, 0.0, "병가"),
        ]
        leave_type_objs = {}
        for name, code, is_paid, is_deductible, deduction_days, default_days, desc in leave_types:
            lt = LeaveType(
                name=name, code=code, is_paid=is_paid, is_deductible=is_deductible,
                deduction_days=deduction_days, default_days=default_days, description=desc,
            )
            db.add(lt)
            db.flush()
            leave_type_objs[code] = lt

        # Create annual leave balance for all users for 2026
        all_users = db.query(User).all()
        annual_type = leave_type_objs["ANNUAL"]
        for u in all_users:
            lb = LeaveBalance(
                user_id=u.id, leave_type_id=annual_type.id,
                year=2026, total_days=15.0, used_days=0.0,
            )
            db.add(lb)

        # === 8. Notice Categories ===
        notice_cats = [
            ("인사", "HR", 1), ("총무", "GA", 2), ("IT", "IT", 3),
            ("경영", "MGMT_NOTICE", 4), ("기타", "ETC", 5),
        ]
        for name, code, order in notice_cats:
            db.add(NoticeCategory(name=name, code=code, sort_order=order))

        # === 9. Work Schedule ===
        db.add(WorkSchedule(
            name="기본근무", start_time="09:00", end_time="18:00",
            lunch_start="12:00", lunch_end="13:00", is_flexible=False,
        ))

        # === 10. Overtime Policy ===
        db.add(OvertimePolicy(
            name="주 52시간", max_weekly_hours=52.0, max_overtime_hours=12.0, is_active=True,
        ))

        # === 11. Document Templates ===
        templates = [
            ("품의서", "일반 품의서", "일반",
             json.dumps({"fields": [{"name": "title", "type": "text"}, {"name": "content", "type": "textarea"}, {"name": "amount", "type": "number"}]}, ensure_ascii=False), 1),
            ("지출결의서", "지출 결의를 위한 양식", "재무",
             json.dumps({"fields": [{"name": "purpose", "type": "text"}, {"name": "amount", "type": "number"}, {"name": "account", "type": "text"}]}, ensure_ascii=False), 2),
            ("휴가신청서", "휴가 신청 양식", "인사",
             json.dumps({"fields": [{"name": "leave_type", "type": "select"}, {"name": "start_date", "type": "date"}, {"name": "end_date", "type": "date"}, {"name": "reason", "type": "textarea"}]}, ensure_ascii=False), 3),
            ("출장신청서", "출장 신청 양식", "일반",
             json.dumps({"fields": [{"name": "destination", "type": "text"}, {"name": "purpose", "type": "textarea"}, {"name": "start_date", "type": "date"}, {"name": "end_date", "type": "date"}, {"name": "budget", "type": "number"}]}, ensure_ascii=False), 4),
            ("업무보고서", "업무 보고 양식", "일반",
             json.dumps({"fields": [{"name": "period", "type": "text"}, {"name": "content", "type": "textarea"}, {"name": "plan", "type": "textarea"}]}, ensure_ascii=False), 5),
        ]
        for name, desc, category, fields, order in templates:
            db.add(DocumentTemplate(
                name=name, description=desc, category=category,
                fields_schema_json=fields, is_active=True, sort_order=order,
            ))

        # === 12. Asset Categories ===
        hw = AssetCategory(name="하드웨어", code="HW", parent_id=None, level=0, sort_order=1)
        sw = AssetCategory(name="소프트웨어", code="SW", parent_id=None, level=0, sort_order=2)
        db.add_all([hw, sw])
        db.flush()

        hw_subs = [
            ("서버", "HW_SERVER", 1), ("네트워크", "HW_NETWORK", 2),
            ("데스크톱", "HW_DESKTOP", 3), ("노트북", "HW_LAPTOP", 4),
            ("모니터", "HW_MONITOR", 5), ("프린터", "HW_PRINTER", 6),
            ("스캐너", "HW_SCANNER", 7),
        ]
        for name, code, order in hw_subs:
            db.add(AssetCategory(name=name, code=code, parent_id=hw.id, level=1, sort_order=order))

        sw_subs = [
            ("OS", "SW_OS", 1), ("오피스", "SW_OFFICE", 2), ("개발도구", "SW_DEV", 3),
        ]
        for name, code, order in sw_subs:
            db.add(AssetCategory(name=name, code=code, parent_id=sw.id, level=1, sort_order=order))

        # === 13. Free Board ===
        db.add(Board(name="자유게시판", description="자유롭게 글을 작성하는 게시판", type="FREE"))

        # === 14. 2026 Korean Holidays ===
        holidays_2026 = [
            ("2026-01-01", "신정", "PUBLIC"),
            ("2026-01-28", "설날 연휴", "PUBLIC"),
            ("2026-01-29", "설날", "PUBLIC"),
            ("2026-01-30", "설날 연휴", "PUBLIC"),
            ("2026-03-01", "삼일절", "PUBLIC"),
            ("2026-05-05", "어린이날", "PUBLIC"),
            ("2026-05-24", "부처님오신날", "PUBLIC"),
            ("2026-06-06", "현충일", "PUBLIC"),
            ("2026-08-15", "광복절", "PUBLIC"),
            ("2026-09-24", "추석 연휴", "PUBLIC"),
            ("2026-09-25", "추석", "PUBLIC"),
            ("2026-09-26", "추석 연휴", "PUBLIC"),
            ("2026-10-03", "개천절", "PUBLIC"),
            ("2026-10-09", "한글날", "PUBLIC"),
            ("2026-12-25", "크리스마스", "PUBLIC"),
        ]
        for date, name, htype in holidays_2026:
            db.add(Holiday(date=date, name=name, type=htype, year=2026))

        db.commit()
        print("Database initialized with seed data.")

    except Exception as e:
        db.rollback()
        print(f"Error initializing database: {e}")
        raise
    finally:
        db.close()

"""
Load fixture JSON files into the groupware database.
Run after init_data.py has seeded the base data.

Usage: python -m fixtures.load_fixtures
"""
import json
import os
import sys
from datetime import datetime, timezone
from uuid import uuid4

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.organization import Department, Position, Title, UserDepartment
from app.models.role import Role
from app.models.approval import DocumentTemplate, ApprovalDocument, ApprovalLine, ApprovalReference
from app.models.board import NoticeCategory, Notice, NoticeRead, Board, Post
from app.models.attachment import Attachment, Comment
from app.models.attendance import AttendanceRecord, WorkSchedule, Holiday
from app.models.leave import LeaveType, LeaveBalance, LeaveRequest
from app.models.overtime import OvertimeRequest, OvertimePolicy, WeeklyWorkSummary
from app.models.asset import AssetCategory, Asset, AssetHistory, AssetAssignment

FIXTURES_DIR = os.path.dirname(os.path.abspath(__file__))


def load_json(filename):
    filepath = os.path.join(FIXTURES_DIR, filename)
    if not os.path.exists(filepath):
        print(f"  [WARNING] Fixture file not found: {filename}")
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def get_user_by_name(db, name):
    return db.query(User).filter(User.name == name).first()


def get_template_by_name(db, name):
    return db.query(DocumentTemplate).filter(DocumentTemplate.name == name).first()


def get_category_by_code(db, code):
    return db.query(NoticeCategory).filter(NoticeCategory.code == code).first()


def get_leave_type_by_code(db, code):
    return db.query(LeaveType).filter(LeaveType.code == code).first()


def get_asset_category_by_code(db, code):
    return db.query(AssetCategory).filter(AssetCategory.code == code).first()


def get_board_by_name(db, name):
    return db.query(Board).filter(Board.name == name).first()


# ---------------------------------------------------------------------------
# Fixture loaders
# ---------------------------------------------------------------------------

def load_attendance(db):
    data = load_json("attendance.json")
    if data is None:
        return

    now = datetime.now(timezone.utc).isoformat()
    records = data if isinstance(data, list) else data.get("records", data.get("attendance", []))

    for rec in records:
        user = get_user_by_name(db, rec["user_name"])
        if not user:
            print(f"  [WARNING] User not found: {rec['user_name']} - skipping attendance record")
            continue

        ar = AttendanceRecord(
            user_id=user.id,
            date=rec["date"],
            check_in_at=rec.get("check_in_at"),
            check_out_at=rec.get("check_out_at"),
            work_minutes=rec.get("work_minutes"),
            status=rec.get("status", "NORMAL"),
            note=rec.get("note"),
            created_at=now,
            updated_at=now,
        )
        db.add(ar)

    db.flush()


def load_leaves(db):
    data = load_json("leaves.json")
    if data is None:
        return

    now = datetime.now(timezone.utc).isoformat()

    # Load leave requests
    requests = data if isinstance(data, list) else data.get("requests", [])
    for req in requests:
        user = get_user_by_name(db, req["user_name"])
        if not user:
            print(f"  [WARNING] User not found: {req['user_name']} - skipping leave request")
            continue

        lt_code = req.get("leave_type_code") or req.get("leave_type")
        leave_type = get_leave_type_by_code(db, lt_code)
        if not leave_type:
            print(f"  [WARNING] Leave type not found: {lt_code} - skipping")
            continue

        approver = None
        if req.get("approver_name"):
            approver = get_user_by_name(db, req["approver_name"])
            if not approver:
                print(f"  [WARNING] Approver not found: {req['approver_name']}")

        lr = LeaveRequest(
            user_id=user.id,
            leave_type_id=leave_type.id,
            start_date=req["start_date"],
            end_date=req["end_date"],
            days=req["days"],
            reason=req.get("reason"),
            status=req.get("status", "PENDING"),
            approver_id=approver.id if approver else None,
            created_at=now,
            updated_at=now,
        )
        db.add(lr)

    db.flush()

    # Update leave balances - supports both dict {name: days} and list format
    raw_updates = data.get("balance_updates", {}) if isinstance(data, dict) else {}
    annual_type = get_leave_type_by_code(db, "ANNUAL")
    if isinstance(raw_updates, dict) and annual_type:
        for user_name, used_days in raw_updates.items():
            user = get_user_by_name(db, user_name)
            if not user:
                print(f"  [WARNING] User not found for balance update: {user_name}")
                continue
            balance = db.query(LeaveBalance).filter(
                LeaveBalance.user_id == user.id,
                LeaveBalance.leave_type_id == annual_type.id,
                LeaveBalance.year == 2026,
            ).first()
            if balance:
                balance.used_days = used_days
                balance.updated_at = now
            else:
                print(f"  [WARNING] Leave balance not found for {user_name}")

    db.flush()


def load_overtime(db):
    data = load_json("overtime.json")
    if data is None:
        return

    now = datetime.now(timezone.utc).isoformat()

    # Load overtime requests
    requests = data if isinstance(data, list) else data.get("requests", [])
    for req in requests:
        user = get_user_by_name(db, req["user_name"])
        if not user:
            print(f"  [WARNING] User not found: {req['user_name']} - skipping overtime request")
            continue

        approver = None
        if req.get("approver_name"):
            approver = get_user_by_name(db, req["approver_name"])
            if not approver:
                print(f"  [WARNING] Approver not found: {req['approver_name']}")

        ot = OvertimeRequest(
            user_id=user.id,
            date=req["date"],
            type=req.get("type") or req.get("overtime_type", "OVERTIME"),
            planned_start=req.get("planned_start") or req.get("start_at"),
            planned_end=req.get("planned_end") or req.get("end_at"),
            planned_hours=req.get("planned_hours") or req.get("hours"),
            reason=req.get("reason"),
            status=req.get("status", "PENDING"),
            approver_id=approver.id if approver else None,
            created_at=now,
            updated_at=now,
        )
        db.add(ot)

    db.flush()

    # Load weekly summaries
    weekly_summaries = data.get("weekly_summaries", []) if isinstance(data, dict) else []
    for ws in weekly_summaries:
        user = get_user_by_name(db, ws["user_name"])
        if not user:
            print(f"  [WARNING] User not found: {ws['user_name']} - skipping weekly summary")
            continue

        summary = WeeklyWorkSummary(
            user_id=user.id,
            year=ws["year"],
            week_number=ws.get("week_number") or ws.get("week"),
            regular_hours=ws.get("regular_hours", 0.0),
            overtime_hours=ws.get("overtime_hours", 0.0),
            total_hours=ws.get("total_hours", 0.0),
            is_exceeded=ws.get("is_exceeded", False),
            created_at=now,
            updated_at=now,
        )
        db.add(summary)

    db.flush()


def load_approvals(db):
    data = load_json("approvals.json")
    if data is None:
        return

    now = datetime.now(timezone.utc).isoformat()
    documents = data if isinstance(data, list) else data.get("documents", [])

    for idx, doc in enumerate(documents):
        template = None
        if doc.get("template_name"):
            template = get_template_by_name(db, doc["template_name"])
            if not template:
                print(f"  [WARNING] Template not found: {doc['template_name']}")

        submitter = get_user_by_name(db, doc["submitted_by_name"])
        if not submitter:
            print(f"  [WARNING] User not found: {doc['submitted_by_name']} - skipping approval document")
            continue

        doc_number = doc.get("document_number", f"APR-2026-{idx + 1:05d}")

        content_json = doc.get("content_json")
        if content_json and not isinstance(content_json, str):
            content_json = json.dumps(content_json, ensure_ascii=False)

        approval_doc = ApprovalDocument(
            document_number=doc_number,
            template_id=template.id if template else None,
            title=doc["title"],
            content_json=content_json,
            status=doc.get("status", "DRAFT"),
            urgency=doc.get("urgency", "NORMAL"),
            submitted_by=submitter.id,
            submitted_at=doc.get("submitted_at"),
            completed_at=doc.get("completed_at"),
            created_at=now,
            updated_at=now,
        )
        db.add(approval_doc)
        db.flush()

        # Approval lines
        for line in doc.get("lines", []):
            approver = get_user_by_name(db, line["approver_name"])
            if not approver:
                print(f"  [WARNING] Approver not found: {line['approver_name']} - skipping approval line")
                continue

            al = ApprovalLine(
                document_id=approval_doc.id,
                approver_id=approver.id,
                step_order=line.get("step_order", 0),
                line_type=line.get("line_type", "SEQUENTIAL"),
                status=line.get("status", "PENDING"),
                comment=line.get("comment"),
                acted_at=line.get("acted_at"),
                created_at=now,
                updated_at=now,
            )
            db.add(al)

        # References (optional)
        for ref in doc.get("references", []):
            ref_user = get_user_by_name(db, ref["user_name"])
            if not ref_user:
                print(f"  [WARNING] Reference user not found: {ref['user_name']}")
                continue

            ar = ApprovalReference(
                document_id=approval_doc.id,
                user_id=ref_user.id,
                is_read=ref.get("is_read", False),
                created_at=now,
            )
            db.add(ar)

    db.flush()


def load_notices(db):
    data = load_json("notices.json")
    if data is None:
        return

    now = datetime.now(timezone.utc).isoformat()
    notices = data if isinstance(data, list) else data.get("notices", [])

    for n in notices:
        category = None
        if n.get("category_code"):
            category = get_category_by_code(db, n["category_code"])
            if not category:
                print(f"  [WARNING] Notice category not found: {n['category_code']}")

        author = get_user_by_name(db, n["author_name"])
        if not author:
            print(f"  [WARNING] User not found: {n['author_name']} - skipping notice")
            continue

        notice = Notice(
            title=n["title"],
            content=n["content"],
            category_id=category.id if category else None,
            author_id=author.id,
            is_pinned=n.get("is_pinned", False),
            is_must_read=n.get("is_must_read", False),
            view_count=n.get("view_count", 0),
            created_at=n.get("created_at", now),
            updated_at=n.get("updated_at", now),
        )
        db.add(notice)

    db.flush()


def load_posts(db):
    data = load_json("posts.json")
    if data is None:
        return

    now = datetime.now(timezone.utc).isoformat()

    # Load posts
    posts_data = data if isinstance(data, list) else data.get("posts", [])
    created_posts = []

    for p in posts_data:
        board = get_board_by_name(db, p.get("board_name", "자유게시판"))
        if not board:
            print(f"  [WARNING] Board not found: {p.get('board_name', '자유게시판')} - skipping post")
            created_posts.append(None)
            continue

        author = get_user_by_name(db, p["author_name"])
        if not author:
            print(f"  [WARNING] User not found: {p['author_name']} - skipping post")
            created_posts.append(None)
            continue

        post = Post(
            board_id=board.id,
            title=p["title"],
            content=p["content"],
            author_id=author.id,
            is_pinned=p.get("is_pinned", False),
            view_count=p.get("view_count", 0),
            created_at=p.get("created_at", now),
            updated_at=p.get("updated_at", now),
        )
        db.add(post)
        db.flush()
        created_posts.append(post)

    # Load comments
    comments_data = data.get("comments", []) if isinstance(data, dict) else []
    created_comments = []

    for c in comments_data:
        post_index = c.get("post_index", 0)
        if post_index >= len(created_posts) or created_posts[post_index] is None:
            print(f"  [WARNING] Invalid post_index: {post_index} - skipping comment")
            created_comments.append(None)
            continue

        author = get_user_by_name(db, c["author_name"])
        if not author:
            print(f"  [WARNING] User not found: {c['author_name']} - skipping comment")
            created_comments.append(None)
            continue

        parent_id = None
        if c.get("parent_index") is not None:
            parent_index = c["parent_index"]
            if parent_index < len(created_comments) and created_comments[parent_index] is not None:
                parent_id = created_comments[parent_index].id
            else:
                print(f"  [WARNING] Invalid parent_index: {parent_index} - creating as top-level comment")

        comment = Comment(
            commentable_type="post",
            commentable_id=created_posts[post_index].id,
            parent_id=parent_id,
            content=c["content"],
            author_id=author.id,
            created_at=c.get("created_at", now),
            updated_at=c.get("updated_at", now),
        )
        db.add(comment)
        db.flush()
        created_comments.append(comment)

    db.flush()


def load_assets(db):
    data = load_json("assets.json")
    if data is None:
        return

    now = datetime.now(timezone.utc).isoformat()

    # Load assets
    assets_data = data if isinstance(data, list) else data.get("assets", [])
    created_assets = []

    for a in assets_data:
        category = None
        if a.get("category_code"):
            category = get_asset_category_by_code(db, a["category_code"])
            if not category:
                print(f"  [WARNING] Asset category not found: {a['category_code']}")

        spec_json = a.get("spec_json")
        if spec_json and not isinstance(spec_json, str):
            spec_json = json.dumps(spec_json, ensure_ascii=False)

        asset = Asset(
            asset_number=a["asset_number"],
            category_id=category.id if category else None,
            name=a["name"],
            manufacturer=a.get("manufacturer"),
            model=a.get("model"),
            serial_number=a.get("serial_number"),
            spec_json=spec_json,
            purchase_date=a.get("purchase_date"),
            purchase_price=a.get("purchase_price"),
            location=a.get("location"),
            status=a.get("status", "AVAILABLE"),
            image_url=a.get("image_url"),
            created_at=now,
            updated_at=now,
        )
        db.add(asset)
        db.flush()
        created_assets.append(asset)

    # Load assignments
    assignments_data = data.get("assignments", []) if isinstance(data, dict) else []
    for asgn in assignments_data:
        asset_index = asgn.get("asset_index", 0)
        if asset_index >= len(created_assets):
            print(f"  [WARNING] Invalid asset_index: {asset_index} - skipping assignment")
            continue

        asset = created_assets[asset_index]

        assignee_name = asgn.get("user_name") or asgn.get("assignee_name")
        user = get_user_by_name(db, assignee_name)
        if not user:
            print(f"  [WARNING] User not found: {assignee_name} - skipping asset assignment")
            continue

        assigner = get_user_by_name(db, asgn.get("assigned_by_name", "관리자"))
        if not assigner:
            print(f"  [WARNING] Assigner not found: {asgn.get('assigned_by_name', '관리자')}")
            continue

        assignment = AssetAssignment(
            asset_id=asset.id,
            assignee_type=asgn.get("assignee_type", "USER"),
            assignee_id=user.id,
            assigned_by=assigner.id,
            assigned_at=asgn.get("assigned_at", now),
            returned_at=asgn.get("returned_at"),
            is_active=asgn.get("is_active", True),
            created_at=now,
            updated_at=now,
        )
        db.add(assignment)
        db.flush()

        # Create history entry for assignment
        history = AssetHistory(
            asset_id=asset.id,
            action="ASSIGNED",
            from_value=None,
            to_value=user.name,
            performed_by=assigner.id,
            performed_at=asgn.get("assigned_at", now),
            note=asgn.get("note", f"{user.name}에게 자산 배정"),
            created_at=now,
        )
        db.add(history)

        # Update asset status if actively assigned
        if asgn.get("is_active", True):
            asset.status = "IN_USE"

    db.flush()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    db = SessionLocal()
    try:
        # Check if fixtures already loaded
        if db.query(Notice).first():
            print("Fixtures already loaded. Skipping.")
            return

        print("Loading fixtures...")

        try:
            load_attendance(db)
            print("  ✓ Attendance records loaded")
        except Exception as e:
            print(f"  ✗ Error loading attendance: {e}")

        try:
            load_leaves(db)
            print("  ✓ Leave requests loaded")
        except Exception as e:
            print(f"  ✗ Error loading leaves: {e}")

        try:
            load_overtime(db)
            print("  ✓ Overtime data loaded")
        except Exception as e:
            print(f"  ✗ Error loading overtime: {e}")

        try:
            load_approvals(db)
            print("  ✓ Approval documents loaded")
        except Exception as e:
            print(f"  ✗ Error loading approvals: {e}")

        try:
            load_notices(db)
            print("  ✓ Notices loaded")
        except Exception as e:
            print(f"  ✗ Error loading notices: {e}")

        try:
            load_posts(db)
            print("  ✓ Posts and comments loaded")
        except Exception as e:
            print(f"  ✗ Error loading posts: {e}")

        try:
            load_assets(db)
            print("  ✓ Assets loaded")
        except Exception as e:
            import traceback; traceback.print_exc()
            print(f"  ✗ Error loading assets: {e}")

        db.commit()
        print("\nAll fixtures loaded successfully!")
    except Exception as e:
        db.rollback()
        print(f"\nError loading fixtures: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

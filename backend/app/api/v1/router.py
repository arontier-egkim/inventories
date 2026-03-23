from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    users,
    organizations,
    roles,
    approvals,
    templates,
    notices,
    boards,
    attachments,
    comments,
    attendance,
    holidays,
    leaves,
    overtime,
    assets,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(organizations.router)
api_router.include_router(roles.router)
api_router.include_router(approvals.router)
api_router.include_router(templates.router)
api_router.include_router(notices.router)
api_router.include_router(boards.router)
api_router.include_router(attachments.router)
api_router.include_router(comments.router)
api_router.include_router(attendance.router)
api_router.include_router(holidays.router)
api_router.include_router(leaves.router)
api_router.include_router(overtime.router)
api_router.include_router(assets.router)

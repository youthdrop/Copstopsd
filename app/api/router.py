from fastapi import APIRouter

from app.api.routes import (
    auth,
    complaints,
    officers,
    case_notes,
    users,
    password_reset,
    public,   # ✅ ADD THIS
)

router = APIRouter()

router.include_router(auth.router)
router.include_router(complaints.router)
router.include_router(officers.router)
router.include_router(case_notes.router)
router.include_router(users.router)
router.include_router(password_reset.router)
router.include_router(public.router)  # ✅ ADD THIS

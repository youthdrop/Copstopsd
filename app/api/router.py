from fastapi import APIRouter

from app.api.routes import (
    auth,
    complaints,
    officers,
    case_notes,
    public,   # ✅ ADD THIS
)

router = APIRouter()

router.include_router(auth.router)
router.include_router(complaints.router)
router.include_router(officers.router)
router.include_router(case_notes.router)
router.include_router(public.router)  # ✅ ADD THIS

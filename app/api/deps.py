from __future__ import annotations
from fastapi import Depends, Header, HTTPException
from typing import Optional

# MVP auth placeholder:
# Provide X-Staff-Key header to allow staff endpoints.
# Replace with proper JWT later.
STAFF_KEY = "dev-staff-key"

def require_staff(x_staff_key: Optional[str] = Header(default=None)):
    if x_staff_key != STAFF_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized (missing/invalid X-Staff-Key)")
    return True

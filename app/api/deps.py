from __future__ import annotations

import os
from typing import Optional

from fastapi import Header, HTTPException


def require_staff(x_staff_key: Optional[str] = Header(default=None, alias="X-Staff-Key")):
  """
  Staff-only gate.
  Frontend must send header: X-Staff-Key: <value>
  The expected value comes from env STAFF_KEY (Railway). Falls back to dev-staff-key locally.
  """
  expected = os.getenv("STAFF_KEY", "dev-staff-key")

  if not x_staff_key or x_staff_key != expected:
    # 401 is correct for missing/invalid credentials
    raise HTTPException(status_code=401, detail="Unauthorized (missing/invalid X-Staff-Key)")
  return True

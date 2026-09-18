"""
RailOpt Authentication API — Prototype Role-Based Session
===========================================================
Provides login with Division + Role selection for SIH 2026 judges.
No real password enforcement — prototype credential system.
Token = base64-encoded JSON profile (demo-grade, sufficient for judging).
"""

import base64
import json
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/auth", tags=["Authentication"])

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Valid Divisions (Indian Railways operational divisions)
# ---------------------------------------------------------------------------
VALID_DIVISIONS = {
    "NDL": "Northern Railway — Delhi Division",
    "NW":  "North Central Railway — Prayagraj (NCR)",
    "NCR": "North Central Railway — Prayagraj (NCR)",
    "WR":  "Western Railway — Mumbai Central Division",
    "CR":  "Central Railway — Mumbai CST Division",
    "ER":  "Eastern Railway — Howrah Division",
    "SER": "South Eastern Railway — Kharagpur Division",
    "SCR": "South Central Railway — Secunderabad Division",
    "SR":  "Southern Railway — Chennai Division",
    "NWR": "North Western Railway — Jaipur Division",
    "NER": "North Eastern Railway — Gorakhpur Division",
}

# ---------------------------------------------------------------------------
# Valid Roles — mapped to display name + permissions
# ---------------------------------------------------------------------------
VALID_ROLES = {
    "CONTROLLER":  {"label": "Controller (DOM/TPC)", "can_approve": True,  "can_optimize": True,  "can_edit": True, "initial": "C"},
    "PLANNER":     {"label": "Planner (Sr. DOM)",    "can_approve": True,  "can_optimize": True,  "can_edit": True, "initial": "P"},
    "ENGINEER":    {"label": "Engineer (JE/SSE ENG)","can_approve": False, "can_optimize": False, "can_edit": True, "initial": "E"},
    "TRD_OFFICER": {"label": "TRD Officer (OHE/TPC)","can_approve": False, "can_optimize": False, "can_edit": True, "initial": "T"},
    "ST_OFFICER":  {"label": "S&T Officer (Signal)", "can_approve": False, "can_optimize": False, "can_edit": True, "initial": "S"},
}

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class LoginRequest(BaseModel):
    username: str = "railopt_user"
    role: str = "PLANNER"
    division_code: str = "NDL"


class LoginResponse(BaseModel):
    token: str
    user_profile: dict


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _encode_token(profile: dict) -> str:
    """Encode user profile as a base64 demo token."""
    return base64.b64encode(json.dumps(profile).encode()).decode()


def _decode_token(token: str) -> Optional[dict]:
    """Decode base64 demo token back to profile dict."""
    try:
        return json.loads(base64.b64decode(token.encode()).decode())
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest):
    """
    Prototype login — validates role and division, returns demo token + user profile.
    No password required (SIH judging demo).
    """
    role_upper = req.role.upper()
    div_upper = req.division_code.upper()

    if role_upper not in VALID_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role '{req.role}'. Valid roles: {list(VALID_ROLES.keys())}"
        )

    if div_upper not in VALID_DIVISIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid division code '{req.division_code}'. Valid codes: {list(VALID_DIVISIONS.keys())}"
        )

    role_info = VALID_ROLES[role_upper]
    division_name = VALID_DIVISIONS[div_upper]

    profile = {
        "username": req.username or "railopt_user",
        "role": role_upper,
        "role_label": role_info["label"],
        "division_code": div_upper,
        "division_name": division_name,
        "can_approve": role_info["can_approve"],
        "can_optimize": role_info["can_optimize"],
        "can_edit": role_info["can_edit"],
        "initial": role_info.get("initial", (req.username or "R")[0].upper()),
        "corridor": f"{division_name} Mainline Corridor",
    }

    token = _encode_token(profile)
    return LoginResponse(token=token, user_profile=profile)


@router.get("/me")
def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """
    Decode and return the current user profile from Authorization header.
    Header format: Authorization: Bearer <token>
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header."
        )

    token = authorization[len("Bearer "):].strip()
    profile = _decode_token(token)
    if not profile or not isinstance(profile, dict) or "role" not in profile:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session token."
        )

    return profile


def require_permission(permission: str):
    """
    FastAPI dependency factory enforcing that the authenticated user possesses
    the specified boolean permission flag (e.g. 'can_approve', 'can_optimize').
    """
    def permission_checker(current_user: dict = Depends(get_current_user)) -> dict:
        if not current_user.get(permission, False):
            role_name = current_user.get("role", "UNKNOWN")
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied. Role '{role_name}' does not have '{permission}' permission."
            )
        return current_user
    return permission_checker


def validate_department_scope(user: dict, requested_dept_code: str):
    """
    Validates that field submitters (Engineer, TRD Officer, S&T Officer)
    only create, edit, or delete requests for their designated department.
    Controllers and Planners have system-wide department access.
    """
    role = user.get("role", "").upper()
    dept_upper = requested_dept_code.upper()

    department_role_map = {
        "ENGINEER": ["ENG"],
        "TRD_OFFICER": ["TRD"],
        "ST_OFFICER": ["S_T", "ST", "S&T"]
    }

    if role in department_role_map:
        allowed_depts = department_role_map[role]
        if dept_upper not in allowed_depts:
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied. Role '{role}' cannot operate on department '{requested_dept_code}' (authorized scope: {allowed_depts})."
            )


@router.get("/divisions")
def list_divisions():
    """Return all valid Indian Railways divisions for the login form dropdown."""
    return [{"code": k, "name": v} for k, v in VALID_DIVISIONS.items()]


@router.get("/roles")
def list_roles():
    """Return all valid roles for the login form dropdown."""
    return [
        {"code": k, "label": v["label"], "can_approve": v["can_approve"]}
        for k, v in VALID_ROLES.items()
    ]


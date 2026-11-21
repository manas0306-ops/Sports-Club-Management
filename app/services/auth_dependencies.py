"""
FastAPI Authentication & Strict Role-Based Access Control (RBAC) Dependencies
"""
from typing import Optional, List
from fastapi import Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.services.auth_security import (
    SESSION_COOKIE_NAME,
    decode_session_token,
    log_security_event
)

def get_token_from_request(request: Request) -> Optional[str]:
    """Extracts session token from HTTP-only cookie or Authorization header."""
    cookie_token = request.cookies.get(SESSION_COOKIE_NAME)
    if cookie_token:
        return cookie_token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()
    return None

def get_optional_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Returns authenticated User if valid session token exists, else None."""
    token = get_token_from_request(request)
    if not token:
        return None
    
    payload = decode_session_token(token)
    if not payload or not payload.get("sub"):
        return None
    
    user_id = int(payload["sub"])
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        return None
    return user

def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """
    Enforces authentication.
    If unauthenticated:
      - For browser HTML requests: redirects to /login
      - For API requests: raises HTTP 401 Unauthorized
    """
    user = get_optional_current_user(request, db)
    if user:
        return user
    
    accept = request.headers.get("accept", "")
    if "text/html" in accept and not request.url.path.startswith("/api/"):
        login_url = f"/login?next={request.url.path}"
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": login_url}
        )
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Please log in."
    )

def require_role(allowed_roles: List[UserRole]):
    """
    Strict Role Guard.
    Validates user has ONE OF the permitted primary roles.
    If role does not match:
      - Logs UNAUTHORIZED_ACCESS_ATTEMPT in AuditLog
      - Strictly returns HTTP 403 Forbidden (Never exposes dashboard HTML)
    """
    def role_checker(
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        allowed_values = [r.value if isinstance(r, UserRole) else r for r in allowed_roles]
        
        if current_user.primary_role not in allowed_values:
            # Security Audit Log
            log_security_event(
                db=db,
                action="UNAUTHORIZED_ACCESS_ATTEMPT",
                username=current_user.username,
                user_id=current_user.id,
                resource=request.url.path,
                ip_address=request.client.host if request.client else "unknown",
                status="FORBIDDEN",
                details=f"User role '{current_user.primary_role}' attempted accessing restricted scope {allowed_values}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: Insufficient role permissions for {request.url.path}."
            )
        return current_user
    return role_checker

# Reusable Specific Role Dependencies
require_admin = require_role([UserRole.ADMIN])
require_member = require_role([UserRole.MEMBER])
require_player = require_role([UserRole.PLAYER])
require_staff = require_role([UserRole.STAFF])
require_walk_in = require_role([UserRole.WALK_IN])

def require_staff_permission(permission_field: str):
    """
    Granular staff permission check (e.g. can_manage_courts, can_operate_pos).
    Enforces staff role AND specific departmental permission flag.
    """
    def permission_checker(
        request: Request,
        staff_user: User = Depends(require_staff),
        db: Session = Depends(get_db)
    ) -> User:
        emp = staff_user.employee_profile
        if not emp:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No employee profile associated with this staff account."
            )
        
        has_perm = getattr(emp, permission_field, False)
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operational permission denied: requires '{permission_field}'."
            )
        return staff_user
    return permission_checker

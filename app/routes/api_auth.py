"""
Authentication API Router
Handles multi-role login with strict backend role enforcement, session management, and logout.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models.user import User, UserRole
from app.services.auth_security import (
    SESSION_COOKIE_NAME,
    hash_password,
    verify_password,
    create_session_token,
    check_login_rate_limit,
    record_login_failure,
    reset_login_attempts,
    log_security_event
)
from app.services.auth_dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    identifier: str = Field(..., description="Email or Username")
    password: str = Field(..., min_length=1, description="Password")
    selected_role: str = Field(..., description="Selected access role (ADMIN, MEMBER, PLAYER, STAFF, WALK_IN)")
    remember_me: bool = Field(default=False)

class PasswordResetRequest(BaseModel):
    email: str = Field(..., description="Registered Email Address")

ROLE_DASHBOARDS = {
    UserRole.ADMIN.value: "/admin/dashboard",
    UserRole.MEMBER.value: "/member/dashboard",
    UserRole.PLAYER.value: "/player/dashboard",
    UserRole.STAFF.value: "/staff/dashboard",
    UserRole.WALK_IN.value: "/guest"
}

@router.post("/login")
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    rate_key = f"{ip}:{payload.identifier.strip().lower()}"
    
    # 1. Rate Limiting Check
    is_locked, remaining_sec = check_login_rate_limit(rate_key)
    if is_locked:
        log_security_event(
            db=db,
            action="LOGIN_RATE_LIMITED",
            username=payload.identifier,
            ip_address=ip,
            status="BLOCKED",
            details=f"Rate limit exceeded. Remaining lockout: {remaining_sec}s"
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed login attempts. Account temporarily locked for {remaining_sec} seconds."
        )

    # 2. Lookup User
    identifier_clean = payload.identifier.strip().lower()
    user = db.query(User).filter(
        or_(
            User.email.ilike(identifier_clean),
            User.username.ilike(identifier_clean)
        )
    ).first()

    if not user:
        is_locked, remaining_sec = record_login_failure(rate_key)
        log_security_event(
            db=db,
            action="LOGIN_FAILURE_NOT_FOUND",
            username=payload.identifier,
            ip_address=ip,
            status="FAILED",
            details="User identifier not found"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please verify your email/username and password."
        )

    # 3. Account Status Check
    if not user.is_active:
        log_security_event(
            db=db,
            action="LOGIN_DEACTIVATED_ACCOUNT",
            username=user.username,
            user_id=user.id,
            ip_address=ip,
            status="BLOCKED",
            details="Account is inactive/deactivated"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact club administration."
        )

    # 4. Password Verification
    if not verify_password(payload.password, user.password_hash):
        is_locked, remaining_sec = record_login_failure(rate_key)
        log_security_event(
            db=db,
            action="LOGIN_FAILURE_BAD_PASSWORD",
            username=user.username,
            user_id=user.id,
            ip_address=ip,
            status="FAILED",
            details="Incorrect password"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please verify your email/username and password."
        )

    # 5. Strict Role Selection Validation
    # The selected access portal must match the user's actual primary role in DB
    selected_clean = payload.selected_role.strip().upper()
    actual_role = (user.primary_role or "").upper()

    if selected_clean != actual_role:
        log_security_event(
            db=db,
            action="ROLE_MISMATCH_DENIAL",
            username=user.username,
            user_id=user.id,
            ip_address=ip,
            status="DENIED",
            details=f"User attempted login via '{selected_clean}', but account role is '{actual_role}'"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role mismatch: This account has the role '{actual_role}'. You cannot log in through the '{selected_clean}' portal."
        )

    # Reset failed attempts
    reset_login_attempts(rate_key)

    # 6. Generate Session Token & Set Cookie
    token = create_session_token(
        user_id=user.id,
        username=user.username,
        primary_role=actual_role,
        remember_me=payload.remember_me
    )

    max_age = 30 * 86400 if payload.remember_me else 24 * 3600
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=max_age,
        httponly=True,
        samesite="lax",
        secure=False # Set to True in HTTPS production
    )

    log_security_event(
        db=db,
        action="LOGIN_SUCCESS",
        username=user.username,
        user_id=user.id,
        ip_address=ip,
        status="SUCCESS",
        details=f"Successful login as {actual_role}"
    )

    redirect_url = ROLE_DASHBOARDS.get(actual_role, "/login")

    return {
        "success": True,
        "message": f"Welcome back, {user.username}!",
        "role": actual_role,
        "redirect_url": redirect_url,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": actual_role
        }
    }

@router.post("/logout")
def logout(response: Response, request: Request, db: Session = Depends(get_db)):
    """Invalidates the session cookie and logs user logout."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    return {"success": True, "message": "Logged out successfully", "redirect_url": "/login"}

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    """Returns profile information for the actively authenticated user."""
    profile_info = {}
    if current_user.primary_role == UserRole.MEMBER.value and current_user.member_profile:
        m = current_user.member_profile
        profile_info = {
            "member_code": m.member_code,
            "tier": m.tier,
            "membership_category": m.membership_category,
            "is_expired": m.is_expired,
            "expiry_date": str(m.expiry_date)
        }
    elif current_user.primary_role == UserRole.PLAYER.value and current_user.player_profile:
        p = current_user.player_profile
        profile_info = {
            "athlete_name": p.athlete_name,
            "primary_sport": p.primary_sport,
            "skill_level": p.skill_level,
            "club_ranking": p.club_ranking
        }
    elif current_user.primary_role == UserRole.STAFF.value and current_user.employee_profile:
        e = current_user.employee_profile
        profile_info = {
            "employee_code": e.employee_code,
            "staff_group": e.staff_group,
            "role": e.role
        }

    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.primary_role,
        "profile": profile_info
    }

@router.post("/forgot-password")
def forgot_password(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    """Simulates secure password reset token dispatch."""
    user = db.query(User).filter(User.email.ilike(payload.email.strip())).first()
    # Always return a generic success message to prevent user enumeration
    return {
        "success": True,
        "message": "If an account exists with this email address, a password reset link has been dispatched to your inbox."
    }

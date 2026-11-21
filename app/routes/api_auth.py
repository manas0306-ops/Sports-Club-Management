"""
Authentication API Router
Handles multi-role login with strict backend role enforcement, registration,
existing member account activation, password reset, session management, and logout.
"""
import re
from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models.user import User, UserRole
from app.models.member import Member, MemberTier, MemberStatus
from app.models.guardian import Guardian
from app.models.player import PlayerProfile
from app.services.auth_security import (
    SESSION_COOKIE_NAME,
    hash_password,
    verify_password,
    create_session_token,
    revoke_session_token,
    create_password_reset_token,
    verify_password_reset_token,
    consume_password_reset_token,
    check_login_rate_limit,
    record_login_failure,
    reset_login_attempts,
    log_security_event
)
from app.services.auth_dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    identifier: str = Field(..., description="Email, Username, or Member ID (e.g. TC-GOLD-0001)")
    password: str = Field(..., min_length=1, description="Password")
    selected_role: str = Field(..., description="Selected access role (ADMIN, MEMBER, PLAYER, STAFF, WALK_IN)")
    remember_me: bool = Field(default=False)

class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, description="User full legal name")
    email: str = Field(..., min_length=5, description="Email address")
    phone: str = Field(..., min_length=7, description="Phone number")
    password: str = Field(..., min_length=6, description="Password (min 6 chars)")
    confirm_password: str = Field(..., min_length=6, description="Confirm password")
    account_type: str = Field(default="MEMBER", description="MEMBER, PLAYER, or WALK_IN")
    membership_category: Optional[str] = Field(default="SILVER", description="GOLD, SILVER, or UNDERAGE")
    date_of_birth: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    guardian_consent: Optional[bool] = False
    is_existing_member_activation: Optional[bool] = False
    existing_member_code: Optional[str] = None
    terms_consent: bool = Field(default=True)

class MemberActivationRequest(BaseModel):
    member_code: str = Field(..., description="Existing Member ID, e.g. TC-GOLD-0001")
    identifier: str = Field(..., description="Registered Email or Phone Number")
    new_password: str = Field(..., min_length=6, description="Password to set")
    confirm_password: str = Field(..., min_length=6, description="Confirm password")

class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., description="Registered Email Address")

class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=10, description="Reset token received")
    new_password: str = Field(..., min_length=6, description="New secret password")
    confirm_password: str = Field(..., min_length=6, description="Confirm new password")

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
            details=f"Rate limit exceeded. Lockout: {remaining_sec}s"
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed login attempts. Temporarily locked for {remaining_sec} seconds."
        )

    # 2. Lookup User by Email, Username, OR Member Code
    identifier_clean = payload.identifier.strip().lower()
    
    # A. Direct User query (email or username)
    user = db.query(User).filter(
        or_(
            User.email.ilike(identifier_clean),
            User.username.ilike(identifier_clean)
        )
    ).first()

    # B. If not found, check if identifier is a Member Code (e.g. TC-GOLD-0001)
    if not user:
        member = db.query(Member).filter(Member.member_code.ilike(payload.identifier.strip())).first()
        if member and member.user:
            user = member.user

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
            detail="Invalid credentials. Please verify your email/account ID and password."
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
            detail="Invalid credentials. Please verify your email/account ID and password."
        )

    # 5. Strict Role Selection Validation
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

    # Reset failed attempts on success
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
        secure=False
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


@router.post("/register")
def register(payload: RegisterRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    """
    Public Account Registration & Existing Member Activation.
    Strictly forbids self-registration for ADMIN and STAFF roles.
    Integrates existing seeded members to avoid duplicate records.
    """
    ip = request.client.host if request.client else "unknown"

    # 1. Role-specific Registration Guard
    requested_type = payload.account_type.strip().upper()
    if requested_type in ["ADMIN", "STAFF"]:
        log_security_event(
            db=db,
            action="UNAUTHORIZED_REGISTRATION_ATTEMPT",
            username=payload.email,
            ip_address=ip,
            status="BLOCKED",
            details=f"Attempted public self-registration for privileged role {requested_type}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Self-registration is strictly prohibited for {requested_type} roles. Accounts must be provisioned by management."
        )

    if requested_type not in ["MEMBER", "PLAYER", "WALK_IN"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid account type '{requested_type}'. Must be MEMBER, PLAYER, or WALK_IN."
        )

    # 2. Form Validation
    if payload.password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match."
        )

    if len(payload.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters in length."
        )

    if not payload.terms_consent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must review and agree to the club terms and privacy policy."
        )

    email_clean = payload.email.strip().lower()
    phone_clean = payload.phone.strip()

    # 3. Duplicate Account Check
    existing_user = db.query(User).filter(User.email.ilike(email_clean)).first()
    if existing_user and existing_user.is_active and existing_user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account is already registered with this email address. Please sign in or reset your password."
        )

    # 4. Check for Existing Seeded / Offline Member Record
    # Look for match by code, email, or phone
    existing_member = None
    if payload.existing_member_code and payload.existing_member_code.strip():
        existing_member = db.query(Member).filter(Member.member_code.ilike(payload.existing_member_code.strip())).first()
    if not existing_member:
        existing_member = db.query(Member).filter(
            or_(
                Member.email.ilike(email_clean),
                Member.phone == phone_clean
            )
        ).first()

    # CASE A: Existing Member linking / activation
    if existing_member:
        # Check if user already linked
        if existing_member.user:
            user = existing_member.user
            user.password_hash = hash_password(payload.password)
            user.is_active = True
            user.is_verified = True
        else:
            # Create user for this member
            base_user = re.sub(r'[^a-zA-Z0-9_]', '_', existing_member.email.split('@')[0].lower())
            user = User(
                email=existing_member.email,
                username=base_user,
                password_hash=hash_password(payload.password),
                primary_role=UserRole.MEMBER.value if existing_member.tier != "walkin" else UserRole.WALK_IN.value,
                is_active=True,
                is_verified=True
            )
            db.add(user)
            db.flush()
            existing_member.user_id = user.id

        db.commit()
        db.refresh(user)

        log_security_event(
            db=db,
            action="MEMBER_ACCOUNT_ACTIVATION",
            username=user.username,
            user_id=user.id,
            ip_address=ip,
            status="SUCCESS",
            details=f"Linked existing member {existing_member.member_code} ({existing_member.tier})"
        )

    # CASE B: Brand New Registration
    else:
        name_parts = payload.full_name.strip().split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else "Member"
        base_user = re.sub(r'[^a-zA-Z0-9_]', '_', email_clean.split('@')[0])
        
        # Ensure unique username
        candidate_user = base_user
        idx = 1
        while db.query(User).filter(User.username == candidate_user).first():
            candidate_user = f"{base_user}_{idx}"
            idx += 1

        primary_role = requested_type
        user = User(
            email=email_clean,
            username=candidate_user,
            password_hash=hash_password(payload.password),
            primary_role=primary_role,
            is_active=True,
            is_verified=True
        )
        db.add(user)
        db.flush()

        # Create Domain Profile according to role
        if requested_type == "MEMBER":
            category = (payload.membership_category or "SILVER").strip().upper()
            tier_map = {"GOLD": "gold", "SILVER": "silver", "UNDERAGE": "junior"}
            tier_val = tier_map.get(category, "silver")
            is_junior = (category == "UNDERAGE")

            # Unique member code
            count = db.query(Member).count() + 1
            code_prefix = "TC-GOLD" if category == "GOLD" else ("TC-JUN" if is_junior else "TC-SILVER")
            member_code = f"{code_prefix}-{count:04d}"

            member = Member(
                member_code=member_code,
                first_name=first_name,
                last_name=last_name,
                email=email_clean,
                phone=phone_clean,
                tier=tier_val,
                status="active",
                is_junior=is_junior,
                start_date=date.today(),
                expiry_date=date.today() + timedelta(days=365),
                user_id=user.id
            )
            db.add(member)
            db.flush()

            # Handle Junior / Guardian
            if is_junior and payload.guardian_name:
                guardian = Guardian(
                    member_id=member.id,
                    guardian_name=payload.guardian_name.strip(),
                    relationship_type="Parent/Legal Guardian",
                    guardian_phone=payload.guardian_phone or phone_clean,
                    guardian_email=email_clean,
                    consent_signed=bool(payload.guardian_consent),
                    medical_notes="Self-registered junior member"
                )
                db.add(guardian)

        elif requested_type == "PLAYER":
            player = PlayerProfile(
                user_id=user.id,
                athlete_name=payload.full_name.strip(),
                email=email_clean,
                phone=phone_clean,
                primary_sport="Tennis",
                skill_level="Intermediate",
                club_ranking="Unranked Prospect",
                team_name="Champions Academy"
            )
            db.add(player)

        elif requested_type == "WALK_IN":
            count = db.query(Member).count() + 1
            guest_code = f"TC-GUEST-{count:04d}"
            member = Member(
                member_code=guest_code,
                first_name=first_name,
                last_name=last_name,
                email=email_clean,
                phone=phone_clean,
                tier="walkin",
                status="active",
                is_junior=False,
                start_date=date.today(),
                expiry_date=date.today() + timedelta(days=365),
                user_id=user.id
            )
            db.add(member)

        db.commit()
        db.refresh(user)

        log_security_event(
            db=db,
            action="ACCOUNT_REGISTRATION_SUCCESS",
            username=user.username,
            user_id=user.id,
            ip_address=ip,
            status="SUCCESS",
            details=f"New {primary_role} account registered"
        )

    # 5. Automatically create session & log in
    token = create_session_token(
        user_id=user.id,
        username=user.username,
        primary_role=user.primary_role,
        remember_me=False
    )

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=24 * 3600,
        httponly=True,
        samesite="lax",
        secure=False
    )

    redirect_url = ROLE_DASHBOARDS.get(user.primary_role, "/login")

    return {
        "success": True,
        "message": f"Welcome to The Champions Club, {user.username}!",
        "role": user.primary_role,
        "redirect_url": redirect_url,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.primary_role
        }
    }


@router.post("/activate")
def activate_existing_member(payload: MemberActivationRequest, response: Response, db: Session = Depends(get_db)):
    """
    Dedicated activation endpoint for existing seeded members to set/update their web credentials.
    Matches member code and registered email/phone.
    """
    member = db.query(Member).filter(Member.member_code.ilike(payload.member_code.strip())).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member record not found. Please verify your Member ID (e.g. TC-GOLD-0001)."
        )

    # Verify identity against email or phone
    ident = payload.identifier.strip().lower()
    if member.email.lower() != ident and member.phone.replace(" ", "") != ident.replace(" ", ""):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Verification failed. The provided email or phone does not match this membership."
        )

    if payload.new_password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match."
        )

    if len(payload.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters in length."
        )

    # Link or update user
    if member.user:
        user = member.user
        user.password_hash = hash_password(payload.new_password)
        user.is_active = True
        user.is_verified = True
    else:
        base_user = re.sub(r'[^a-zA-Z0-9_]', '_', member.email.split('@')[0].lower())
        user = User(
            email=member.email,
            username=base_user,
            password_hash=hash_password(payload.new_password),
            primary_role=UserRole.MEMBER.value if member.tier != "walkin" else UserRole.WALK_IN.value,
            is_active=True,
            is_verified=True
        )
        db.add(user)
        db.flush()
        member.user_id = user.id

    db.commit()
    db.refresh(user)

    # Create session
    token = create_session_token(user.id, user.username, user.primary_role, remember_me=False)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=24 * 3600,
        httponly=True,
        samesite="lax",
        secure=False
    )

    return {
        "success": True,
        "message": f"Membership {member.member_code} activated! Welcome to the portal.",
        "redirect_url": ROLE_DASHBOARDS.get(user.primary_role, "/member/dashboard")
    }


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Generates a secure, time-limited, single-use password reset token.
    Returns generic message for public safety, plus the token in response for immediate UI testing.
    """
    email_clean = payload.email.strip().lower()
    user = db.query(User).filter(User.email.ilike(email_clean)).first()

    if user and user.is_active:
        token = create_password_reset_token(user.id, user.email)
        log_security_event(
            db=db,
            action="PASSWORD_RESET_REQUESTED",
            username=user.username,
            user_id=user.id,
            status="PENDING",
            details="Password reset token issued"
        )
        return {
            "success": True,
            "message": "Password reset token generated. Please enter your reset token and new password.",
            "reset_token": token # Delivered so the in-modal reset flow works immediately
        }

    return {
        "success": True,
        "message": "If an active account exists with this email address, password reset instructions have been issued."
    }


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Consumes a valid reset token and securely updates the user's password hash.
    """
    token_record = verify_password_reset_token(payload.token.strip())
    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid, expired, or previously used password reset token."
        )

    if payload.new_password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match."
        )

    if len(payload.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters in length."
        )

    user = db.query(User).filter(User.id == token_record["user_id"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated user account not found."
        )

    # Update password
    user.password_hash = hash_password(payload.new_password)
    user.is_active = True
    consume_password_reset_token(payload.token.strip())
    db.commit()

    log_security_event(
        db=db,
        action="PASSWORD_RESET_SUCCESS",
        username=user.username,
        user_id=user.id,
        status="SUCCESS",
        details="Password successfully updated via reset token"
    )

    return {
        "success": True,
        "message": "Your password has been successfully reset! You can now sign in with your new password."
    }


@router.post("/logout")
def logout(response: Response, request: Request, db: Session = Depends(get_db)):
    """Invalidates the session token server-side and clears the cookie."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    if token:
        revoke_session_token(token)

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

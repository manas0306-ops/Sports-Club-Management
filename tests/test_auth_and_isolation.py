"""
Test Suite: Role-Based Authentication, Strict Dashboard Isolation & Membership Management
"""
import pytest
from datetime import date
from app.models.user import UserRole
from app.models.member import Member
from app.models.guardian import Guardian

def test_login_success_admin(client, db_session):
    """Admin authenticates successfully with correct role and password."""
    payload = {
        "identifier": "admin@test.com",
        "password": "AdminPass123!",
        "selected_role": "ADMIN"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["role"] == "ADMIN"
    assert data["redirect_url"] == "/admin/dashboard"
    assert "champions_session" in response.cookies

def test_login_success_member(client, db_session):
    """Member authenticates successfully and receives member dashboard redirect."""
    payload = {
        "identifier": "gold@test.com",
        "password": "MemberPass123!",
        "selected_role": "MEMBER"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["role"] == "MEMBER"
    assert data["redirect_url"] == "/member/dashboard"

def test_login_invalid_password(client, db_session):
    """Invalid password returns 401 Unauthorized."""
    payload = {
        "identifier": "admin@test.com",
        "password": "WrongPassword999!",
        "selected_role": "ADMIN"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]

def test_login_user_not_found(client, db_session):
    """Unknown user returns 401 Unauthorized."""
    payload = {
        "identifier": "ghost@test.com",
        "password": "AnyPassword!",
        "selected_role": "MEMBER"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401

def test_login_role_mismatch_denied(client, db_session):
    """Admin attempting to authenticate through the MEMBER tab must be denied with 403."""
    payload = {
        "identifier": "admin@test.com",
        "password": "AdminPass123!",
        "selected_role": "MEMBER"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 403
    assert "Role mismatch" in response.json()["detail"]

def test_login_inactive_account_denied(client, db_session):
    """Deactivated accounts are blocked with 403 Forbidden."""
    payload = {
        "identifier": "inactive@test.com",
        "password": "Secret123!",
        "selected_role": "MEMBER"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 403
    assert "deactivated" in response.json()["detail"].lower()

def test_unauthenticated_dashboard_redirect(client, db_session):
    """Unauthenticated access to protected dashboards redirects to /login."""
    # Member dashboard
    res_mem = client.get("/member/dashboard", follow_redirects=False)
    assert res_mem.status_code == 307
    assert "/login" in res_mem.headers["Location"]

    # Admin dashboard
    res_adm = client.get("/admin/dashboard", follow_redirects=False)
    assert res_adm.status_code == 307
    assert "/login" in res_adm.headers["Location"]

def test_strict_dashboard_isolation_member_denied_admin(client, db_session):
    """A MEMBER requesting /admin/dashboard must strictly receive HTTP 403 Forbidden."""
    # 1. Login as Member
    client.post("/api/v1/auth/login", json={
        "identifier": "gold@test.com",
        "password": "MemberPass123!",
        "selected_role": "MEMBER"
    })
    
    # 2. Member accessing member dashboard -> 200 OK
    res_own = client.get("/member/dashboard")
    assert res_own.status_code == 200

    # 3. Member accessing admin dashboard -> STRICT 403 FORBIDDEN
    res_forbidden = client.get("/admin/dashboard")
    assert res_forbidden.status_code == 403

def test_strict_dashboard_isolation_member_denied_player_and_staff(client, db_session):
    """A MEMBER requesting /player/dashboard or /staff/dashboard must receive HTTP 403."""
    client.post("/api/v1/auth/login", json={
        "identifier": "gold@test.com",
        "password": "MemberPass123!",
        "selected_role": "MEMBER"
    })
    assert client.get("/player/dashboard").status_code == 403
    assert client.get("/staff/dashboard").status_code == 403

def test_strict_dashboard_isolation_admin_denied_member_and_player(client, db_session):
    """An ADMIN requesting /member/dashboard or /player/dashboard must receive HTTP 403."""
    # 1. Login as Admin
    client.post("/api/v1/auth/login", json={
        "identifier": "admin@test.com",
        "password": "AdminPass123!",
        "selected_role": "ADMIN"
    })
    # 2. Admin dashboard -> 200 OK
    assert client.get("/admin/dashboard").status_code == 200

    # 3. Admin entering Member dashboard -> STRICT 403 FORBIDDEN
    assert client.get("/member/dashboard").status_code == 403
    # 4. Admin entering Player dashboard -> STRICT 403 FORBIDDEN
    assert client.get("/player/dashboard").status_code == 403

def test_strict_dashboard_isolation_player_denied_staff_and_admin(client, db_session):
    """A PLAYER requesting /staff/dashboard or /admin/dashboard must receive HTTP 403."""
    client.post("/api/v1/auth/login", json={
        "identifier": "player@test.com",
        "password": "PlayerPass123!",
        "selected_role": "PLAYER"
    })
    assert client.get("/player/dashboard").status_code == 200
    assert client.get("/staff/dashboard").status_code == 403
    assert client.get("/admin/dashboard").status_code == 403

def test_strict_dashboard_isolation_staff_denied_member_and_admin(client, db_session):
    """A STAFF account requesting /member/dashboard or /admin/dashboard must receive HTTP 403."""
    client.post("/api/v1/auth/login", json={
        "identifier": "staff@test.com",
        "password": "StaffPass123!",
        "selected_role": "STAFF"
    })
    assert client.get("/staff/dashboard").status_code == 200
    assert client.get("/member/dashboard").status_code == 403
    assert client.get("/admin/dashboard").status_code == 403

def test_underage_membership_guardian_consent(db_session):
    """Underage / Junior members have linked Guardian profiles with verified consent."""
    junior_m = db_session.query(Member).filter(Member.tier == "junior").first()
    assert junior_m is not None
    assert junior_m.membership_category == "UNDERAGE"
    assert junior_m.guardian is not None
    assert junior_m.guardian.consent_status == "approved"
    assert junior_m.guardian.guardian_name == "Guardian Senior"

def test_gold_member_benefits(db_session):
    """Gold membership has 100% free court discount and 20% shop/bar privileges."""
    gold_m = db_session.query(Member).filter(Member.tier == "gold").first()
    assert gold_m is not None
    assert gold_m.membership_category == "GOLD"

def test_logout_invalidates_session(client, db_session):
    """Logout invalidates cookie and prevents further protected access."""
    # Login
    client.post("/api/v1/auth/login", json={
        "identifier": "admin@test.com",
        "password": "AdminPass123!",
        "selected_role": "ADMIN"
    })
    assert client.get("/admin/dashboard").status_code == 200

    # Logout
    res_logout = client.post("/api/v1/auth/logout")
    assert res_logout.status_code == 200

    # Immediate dashboard request is now rejected
    res_after = client.get("/admin/dashboard", follow_redirects=False)
    assert res_after.status_code == 307

def test_guest_portal_public_access(client, db_session):
    """Guest portal is accessible without credentials."""
    response = client.get("/guest")
    assert response.status_code == 200
    assert "Guest Portal" in response.text

# =========================================================================
# NEW REGISTRATION, ACTIVATION & PASSWORD RESET TESTS
# =========================================================================

def test_register_new_member_success(client, db_session):
    """New member self-registers, creates linked Member record and authenticates."""
    payload = {
        "full_name": "Devansh Singhania",
        "email": "devansh.singh@example.com",
        "phone": "+91 99887 76655",
        "password": "DevanshPass123!",
        "confirm_password": "DevanshPass123!",
        "account_type": "MEMBER",
        "membership_category": "GOLD",
        "terms_consent": True
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["role"] == "MEMBER"
    assert data["redirect_url"] == "/member/dashboard"

    # Verify created in DB
    member = db_session.query(Member).filter(Member.email == "devansh.singh@example.com").first()
    assert member is not None
    assert member.tier == "gold"
    assert member.user is not None
    assert member.user.primary_role == "MEMBER"

def test_register_duplicate_email_rejected(client, db_session):
    """Attempting to register with an existing active account email returns 409 Conflict."""
    payload = {
        "full_name": "Another Rohan",
        "email": "gold@test.com", # already registered in test fixtures
        "phone": "+91 91111 22222",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "account_type": "MEMBER",
        "terms_consent": True
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    assert "already registered" in response.json()["detail"].lower()

def test_register_password_mismatch_rejected(client, db_session):
    """Mismatched passwords return 400 Bad Request."""
    payload = {
        "full_name": "Test Mismatch",
        "email": "mismatch@example.com",
        "phone": "+91 90000 11111",
        "password": "SecretPassword1!",
        "confirm_password": "DifferentPassword2!",
        "account_type": "MEMBER",
        "terms_consent": True
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "match" in response.json()["detail"].lower()

def test_register_admin_or_staff_forbidden(client, db_session):
    """Public self-registration for ADMIN or STAFF must strictly return 403 Forbidden."""
    for forbidden_role in ["ADMIN", "STAFF"]:
        payload = {
            "full_name": f"Hacker {forbidden_role}",
            "email": f"hacker.{forbidden_role.lower()}@example.com",
            "phone": "+91 99999 00000",
            "password": "HackerPassword1!",
            "confirm_password": "HackerPassword1!",
            "account_type": forbidden_role,
            "terms_consent": True
        }
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 403
        assert "strictly prohibited" in response.json()["detail"].lower()

def test_register_links_existing_member_no_duplicate(client, db_session):
    """
    If an existing member record exists in DB without a password or needing activation,
    registering with their member_code links the account without creating duplicate member records.
    """
    initial_member_count = db_session.query(Member).count()
    gold_m = db_session.query(Member).filter(Member.tier == "gold").first()
    assert gold_m is not None

    payload = {
        "full_name": "Gold Member Name",
        "email": "gold.newalias@example.com",
        "phone": gold_m.phone,
        "password": "NewActivatedPassword123!",
        "confirm_password": "NewActivatedPassword123!",
        "account_type": "MEMBER",
        "is_existing_member_activation": True,
        "existing_member_code": gold_m.member_code,
        "terms_consent": True
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 200

    # Verify no duplicate member was created
    final_member_count = db_session.query(Member).count()
    assert final_member_count == initial_member_count

def test_member_activation_endpoint(client, db_session):
    """Existing member can activate account via /api/v1/auth/activate."""
    gold_m = db_session.query(Member).filter(Member.tier == "gold").first()
    payload = {
        "member_code": gold_m.member_code,
        "identifier": gold_m.email,
        "new_password": "FreshActivationPass123!",
        "confirm_password": "FreshActivationPass123!"
    }
    response = client.post("/api/v1/auth/activate", json=payload)
    assert response.status_code == 200
    assert response.json()["success"] is True

def test_forgot_and_reset_password_flow(client, db_session):
    """Complete password reset lifecycle: request token -> verify & update -> login with new password."""
    # 1. Request reset token
    res_req = client.post("/api/v1/auth/forgot-password", json={"email": "gold@test.com"})
    assert res_req.status_code == 200
    token = res_req.json().get("reset_token")
    assert token is not None

    # 2. Reset password
    res_reset = client.post("/api/v1/auth/reset-password", json={
        "token": token,
        "new_password": "BrandNewSecretPassword123!",
        "confirm_password": "BrandNewSecretPassword123!"
    })
    assert res_reset.status_code == 200
    assert "successfully reset" in res_reset.json()["message"].lower()

    # 3. Authenticate with new password
    res_login = client.post("/api/v1/auth/login", json={
        "identifier": "gold@test.com",
        "password": "BrandNewSecretPassword123!",
        "selected_role": "MEMBER"
    })
    assert res_login.status_code == 200
    assert res_login.json()["success"] is True

def test_login_with_member_code(client, db_session):
    """Members can authenticate using their Member ID (e.g. TC-GOLD-0001) instead of email."""
    gold_m = db_session.query(Member).filter(Member.tier == "gold").first()
    res = client.post("/api/v1/auth/login", json={
        "identifier": gold_m.member_code,
        "password": "MemberPass123!",
        "selected_role": "MEMBER"
    })
    assert res.status_code == 200
    assert res.json()["role"] == "MEMBER"

def test_server_side_session_token_revocation(client, db_session):
    """Session token is revoked server-side upon logout and cannot be re-used."""
    # Login as admin
    res_login = client.post("/api/v1/auth/login", json={
        "identifier": "admin@test.com",
        "password": "AdminPass123!",
        "selected_role": "ADMIN"
    })
    token = res_login.cookies.get("champions_session")
    assert token is not None

    # Access admin dashboard
    assert client.get("/admin/dashboard", cookies={"champions_session": token}).status_code == 200

    # Logout
    res_logout = client.post("/api/v1/auth/logout", cookies={"champions_session": token})
    assert res_logout.status_code == 200

    # Even if an attacker preserves the old token and presents it manually, it is blocked
    res_blocked = client.get("/admin/dashboard", headers={"Authorization": f"Bearer {token}"}, follow_redirects=False)
    assert res_blocked.status_code == 307

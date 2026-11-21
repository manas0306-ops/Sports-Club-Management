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

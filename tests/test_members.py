"""
Unit & Integration Tests for Member Domain (Scene 1)
"""
from datetime import date, timedelta

def test_create_member_gold(client):
    payload = {
        "first_name": "Arjun",
        "last_name": "Rathore",
        "email": "arjun@example.com",
        "phone": "+91 98888 77777",
        "tier": "gold",
        "duration_months": 12
    }
    response = client.post("/api/v1/members/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "TC-GOL-" in data["member_code"]

def test_member_search(client):
    response = client.get("/api/v1/members/search?q=Gold")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["tier"] == "gold"

def test_member_profile_privileges(client, db_session):
    from app.models.member import Member
    m = db_session.query(Member).filter(Member.tier == "gold").first()
    
    response = client.get(f"/api/v1/members/{m.id}")
    assert response.status_code == 200
    profile = response.json()
    assert profile["tier"] == "gold"
    assert profile["privileges"]["court_discount"] == 1.0 # 100% Free
    assert profile["privileges"]["shop_discount"] == 0.20 # 20%
    assert profile["privileges"]["bar_discount"] == 0.20 # 20%

def test_renew_membership(client, db_session):
    from app.models.member import Member
    m = db_session.query(Member).filter(Member.tier == "silver").first()
    old_expiry = m.expiry_date

    response = client.post(f"/api/v1/members/{m.id}/renew", json={"member_id": m.id, "duration_months": 12})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert date.fromisoformat(data["new_expiry"]) > old_expiry

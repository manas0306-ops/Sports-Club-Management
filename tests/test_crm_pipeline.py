"""
CRM Leads Pipeline & Telemetry API Test Suite.
Authored by: Ujjwal Prakash (ujjwalprakash07) - Backend APIs & CRM Systems
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from starlette.testclient import TestClient
from main import app
from database import Session
from models import Lead
from services import compute_lead_score

def test_crm_pipeline():
    client = TestClient(app, headers={"x-club-request": "1"})

    print("--- 1. Testing RBAC Security for CRM Endpoints ---")
    # Member attempts to access CRM API -> Expect 403
    client.post("/api/login", json={"email": "silver@club.com", "password": "password123"})
    res = client.get("/api/crm/stats")
    assert res.status_code == 403, f"Expected 403 for member on /api/crm/stats, got {res.status_code}"
    res = client.get("/api/crm/leads")
    assert res.status_code == 403, f"Expected 403 for member on /api/crm/leads, got {res.status_code}"
    print("✓ CRM API endpoints are securely guarded against non-staff access.")

    print("\n--- 2. Testing Desk Staff Access & CRM Telemetry Metrics ---")
    client.post("/api/login", json={"email": "desk@club.com", "password": "password123"})
    stats_res = client.get("/api/crm/stats")
    assert stats_res.status_code == 200, f"Desk login failed on /api/crm/stats: {stats_res.text}"
    stats = stats_res.json()
    assert stats["total_inquiries"] >= 4300, f"Expected 4300+ inquiries, got {stats['total_inquiries']}"
    assert stats["online_now"] > 0, "Expected active online users"
    assert stats["total_bandwidth_gb"] > 0, "Expected non-zero bandwidth telemetry"
    assert len(stats["top_cities"]) > 0, "Expected top cities data"
    print(f"✓ CRM Stats verified: {stats['total_inquiries']} inquiries, {stats['online_now']} online now, {stats['total_bandwidth_gb']} GB bandwidth.")

    print("\n--- 3. Testing Precision User ID Search & 6h Scope Filter ---")
    # Test default 6h filter
    r6 = client.get("/api/crm/leads?scope=6h&limit=100")
    assert r6.status_code == 200
    leads_6h = r6.json()
    assert leads_6h["total"] > 0, "Expected leads in last 6 hours"
    print(f"✓ 6-hour real-time window returned {leads_6h['total']} active leads.")

    # Test precision search by User ID
    for test_uid in ["USR00001", "USR03593", "USR04300"]:
        r_uid = client.get(f"/api/crm/leads?query={test_uid}")
        assert r_uid.status_code == 200
        data = r_uid.json()
        assert data["total"] >= 1, f"Expected at least 1 match for {test_uid}"
        assert data["leads"][0]["user_code"] == test_uid
    print("✓ Precision search by User ID (USR00001, USR03593, USR04300) verified.")

    # Test lead scoring
    with Session() as db:
        top_online = db.query(Lead).filter_by(status="Online").first()
        if top_online:
            score = compute_lead_score(top_online)
            assert score >= 50, f"Online lead should have score >= 50, got {score}"
            print(f"✓ Lead score computation verified: {top_online.user_code} score = {score}/100.")

    print("\nPASS: CRM Pipeline & Telemetry API tests passed successfully.\n")

if __name__ == "__main__":
    test_crm_pipeline()

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
from datetime import datetime, timedelta
from main import app
from starlette.testclient import TestClient
from database import Session
from models import Booking, Sale, User, Member, Court, Product
from services import clock

def run_tests():
    client = TestClient(app, headers={"x-club-request": "1"})

    print("--- 1. Testing Silver Member (Member RBAC & Privacy) ---")
    res = client.post("/api/login", json={"email": "silver@club.com", "password": "password123"})
    assert res.status_code == 200, f"Silver login failed: {res.text}"
    
    dash = client.get("/dashboard")
    assert dash.status_code == 200
    html = dash.text
    
    # Silver must NOT see Transaction Ledger, Payment Approvals, or Member Directory
    assert 'data-module="ledger"' not in html, "ERROR: Silver member can see Transaction Ledger!"
    assert 'data-module="approvals"' not in html, "ERROR: Silver member can see Payment Approvals!"
    assert 'data-module="directory"' not in html, "ERROR: Silver member can see Member Directory!"
    assert 'data-module="analytics"' not in html, "ERROR: Silver member can see Executive Analytics!"
    assert 'data-module="hr"' not in html, "ERROR: Silver member can see HR module!"
    
    # Silver MUST see their own clubhouse modules
    assert 'data-module="membership"' in html, "Silver member should see My Membership"
    assert 'data-module="courts"' in html, "Silver member should see Reserve Court"
    assert 'data-module="bookings"' in html, "Silver member should see My Bookings"
    assert 'data-module="shop"' in html, "Silver member should see Pro Shop Orders"
    assert 'data-module="orders"' in html, "Silver member should see My Orders"
    assert 'data-module="profile"' in html, "Silver member should see My Profile"
    print("✓ Silver member sees ONLY member modules. No admin ledger, directory, or approvals exposed!")

    print("\n--- 2. Testing API Security Restrictions for Silver Member ---")
    # Silver member attempts to verify or reject payments
    res = client.post("/api/verify_payment", json={"id": 1})
    assert res.status_code == 403, f"Expected 403 on verify_payment for member, got {res.status_code}"
    
    res = client.post("/api/approve_booking", json={"id": 1})
    assert res.status_code == 403, f"Expected 403 on approve_booking for member, got {res.status_code}"
    
    res = client.post("/api/reject_payment", json={"id": 1})
    assert res.status_code == 403, f"Expected 403 on reject_payment for member, got {res.status_code}"
    
    res = client.post("/api/confirm_all_bookings", json={})
    assert res.status_code == 403, f"Expected 403 on confirm_all_bookings for member, got {res.status_code}"
    
    res = client.post("/api/add_user", json={"email": "hacker@club.com", "name": "Hacker", "password": "password123", "role": "owner"})
    assert res.status_code == 403, f"Expected 403 on add_user for member, got {res.status_code}"
    print("✓ Silver member blocked from all admin and approval APIs with HTTP 403 Forbidden!")

    print("\n--- 3. Testing Calculated Bill & Court Booking Workflow for Silver Member ---")
    import time
    with Session() as db:
        court = db.query(Court).filter_by(sport="Tennis").first()
        court_id = court.id
        # Clean up any existing test bookings for this member
        m_silver = db.query(Member).join(User).filter(User.email=="silver@club.com").first()
        if m_silver:
            db.query(Booking).filter_by(member_id=m_silver.id).delete()
            db.commit()
    
    # Find a future booking slot (in 7 days at 14:00)
    slot_time = (clock() + timedelta(days=7)).replace(hour=14, minute=0, second=0, microsecond=0).isoformat()
    
    # Booking with UPI Transaction ID / UTR
    test_utr = "UPI-987654321012"
    res = client.post("/api/book", json={"court_id": court_id, "start": slot_time, "mode": "UPI", "payment_ref": test_utr})
    assert res.status_code == 200, f"Booking with UTR failed: {res.text}"
    data = res.json()
    assert "Pending Admin Verification" in data["message"]
    booking_receipt_id = data["receipt"]
    print("✓ Court booking created with status: PENDING verification.")

    with Session() as db:
        b = db.query(Booking).filter_by(sale_id=booking_receipt_id).first()
        assert b.status == "Pending", f"Expected Booking.status == 'Pending', got {b.status}"
        s = db.get(Sale, booking_receipt_id)
        assert s.status == "Pending", f"Expected Sale.status == 'Pending', got {s.status}"
        assert s.details.get("payment_verified") is False, "Expected payment_verified == False"
        assert s.details.get("payment_ref") == test_utr, "Expected payment_ref recorded"
    print("✓ Database verified: Booking is held as Pending, Payment is unverified.")

    print("\n--- 4. Testing Pro Shop Order with Calculated Bill & UTR ---")
    with Session() as db:
        prod = db.query(Product).filter_by(department="Shop").first()
        prod_id = prod.id
    
    shop_utr = "UPI-555123456789"
    res = client.post("/api/order", json={
        "department": "Shop",
        "cart": [{"id": prod_id, "qty": 1}],
        "fulfilment": "Pickup",
        "mode": "UPI",
        "payment_ref": shop_utr
    })
    assert res.status_code == 200, f"Shop order failed: {res.text}"
    shop_data = res.json()
    assert "Payment Under Review" in shop_data["message"]
    order_receipt_id = shop_data["receipt"]
    
    with Session() as db:
        s_order = db.get(Sale, order_receipt_id)
        assert s_order.status == "Pending"
        assert s_order.details.get("payment_verified") is False
        assert s_order.details.get("payment_ref") == shop_utr
    print("✓ Shop gear order placed with status: PENDING payment review.")

    print("\n--- 5. Testing Front Desk / Admin Approval Workflow ---")
    client.post("/api/logout")
    res = client.post("/api/login", json={"email": "desk@club.com", "password": "password123"})
    assert res.status_code == 200, "Desk login failed"
    
    dash_desk = client.get("/dashboard")
    assert dash_desk.status_code == 200
    desk_html = dash_desk.text
    assert 'data-module="approvals"' in desk_html, "Desk must see Payment Approvals board!"
    assert 'data-module="directory"' in desk_html, "Desk must see Member Directory!"
    assert 'data-module="courts"' in desk_html, "Desk must see Court Schedule!"
    
    # Desk verifies and confirms the court booking payment
    res = client.post("/api/verify_payment", json={"id": booking_receipt_id, "notes": "Approved by Reception desk staff"})
    assert res.status_code == 200, f"Desk verify_payment failed: {res.text}"
    print("✓ Admin verified and confirmed court booking payment.")
    
    # Desk verifies and confirms the shop order payment
    res = client.post("/api/verify_payment", json={"id": order_receipt_id, "notes": "Shop UPI verified on terminal"})
    assert res.status_code == 200, f"Desk verify shop order failed: {res.text}"
    print("✓ Admin verified and confirmed shop order payment.")

    with Session() as db:
        b_confirmed = db.query(Booking).filter_by(sale_id=booking_receipt_id).first()
        assert b_confirmed.status == "Booked", f"Expected Booked, got {b_confirmed.status}"
        s_confirmed = db.get(Sale, booking_receipt_id)
        assert s_confirmed.status == "Paid"
        assert s_confirmed.details.get("payment_verified") is True
        
        s_order_confirmed = db.get(Sale, order_receipt_id)
        assert s_order_confirmed.status == "Paid"
        assert s_order_confirmed.details.get("payment_verified") is True
        assert s_order_confirmed.details.get("state") == "Received"
    print("✓ Database verified: Court booking confirmed as Booked, Shop order confirmed as Paid & Received.")

    print("\n--- 6. Testing Café and Physio Staff Isolation ---")
    # Bar staff
    client.post("/api/logout")
    client.post("/api/login", json={"email": "bar@club.com", "password": "password123"})
    bar_dash = client.get("/dashboard").text
    assert 'data-module="shift"' in bar_dash, "Bar staff should see shift"
    assert 'data-module="tabs"' in bar_dash, "Bar staff should see tabs"
    assert 'data-module="directory"' not in bar_dash, "Bar staff must NOT see Member Directory"
    assert 'data-module="approvals"' not in bar_dash, "Bar staff must NOT see Payment Approvals"
    assert 'data-module="courts"' not in bar_dash, "Bar staff must NOT see Court Schedule"
    print("✓ Café staff isolated to café tools and kitchen queue only.")

    # Physio staff
    client.post("/api/logout")
    client.post("/api/login", json={"email": "physio@club.com", "password": "password123"})
    physio_dash = client.get("/dashboard").text
    assert 'data-module="physio_schedule"' in physio_dash, "Physio should see clinic schedule"
    assert 'data-module="directory"' not in physio_dash, "Physio must NOT see Member Directory"
    assert 'data-module="approvals"' not in physio_dash, "Physio must NOT see Payment Approvals"
    print("✓ Physio staff isolated to clinical appointments and notes.")

    print("\n==============================================")
    print("ALL SECURITY & APPROVAL FLOW TESTS PASSED! 100%")
    print("==============================================")

if __name__ == "__main__":
    run_tests()

"""
Unit & Integration Tests for CRM, Leads, Owner Financials & HR (Scenes 5 & 6)
"""
from datetime import date, timedelta
from app.models.finance import Employee, LeaveRequest

def test_crm_lead_capture_and_conversion(client):
    # 1. Visitor finds club online and submits enquiry
    res_enq = client.post("/api/v1/crm/enquiries", json={
        "name": "Sunita Rao",
        "email": "sunita.rao@example.com",
        "phone": "+91 91234 56780",
        "interested_sport": "tennis",
        "interested_tier": "silver",
        "source": "website_form",
        "notes": "Looking for evening courts"
    })
    assert res_enq.status_code == 200
    lead_id = res_enq.json()["lead_id"]

    # 2. Staff sends Quote
    res_quote = client.post("/api/v1/crm/quotes", json={
        "lead_id": lead_id,
        "tier_proposed": "silver",
        "coaching_addon_fee": 3000.0,
        "discount_amount": 1000.0
    })
    assert res_quote.status_code == 200
    assert "QT-" in res_quote.json()["quote_number"]

    # 3. 1-Click Convert Lead into Official Member
    res_conv = client.post("/api/v1/crm/convert", json={
        "lead_id": lead_id,
        "tier": "silver"
    })
    assert res_conv.status_code == 200
    conv_data = res_conv.json()
    assert conv_data["success"] is True
    assert "TC-SIL-" in conv_data["member_code"]

def test_owner_financial_metrics_consolidation(client):
    response = client.get("/api/v1/finance/metrics?period=month")
    assert response.status_code == 200
    data = response.json()
    assert "total_revenue" in data
    assert "breakdown_by_source" in data
    assert "courts" in data["breakdown_by_source"]
    assert "shop" in data["breakdown_by_source"]
    assert "bar" in data["breakdown_by_source"]
    assert "breakdown_by_payment_method" in data
    assert "cash" in data["breakdown_by_payment_method"]
    assert "card" in data["breakdown_by_payment_method"]
    assert "upi" in data["breakdown_by_payment_method"]
    assert "online" in data["breakdown_by_payment_method"]

def test_hr_leave_approval(client, db_session):
    emp = Employee(
        employee_code="TEST-EMP",
        name="Test Worker",
        role="bartender",
        email="worker@champions.in",
        phone="+91 99999 00000"
    )
    db_session.add(emp)
    db_session.commit()

    leave = LeaveRequest(
        employee_id=emp.id,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=1),
        reason="Medical checkup",
        status="pending"
    )
    db_session.add(leave)
    db_session.commit()

    res_action = client.post("/api/v1/finance/hr/leaves/action", json={
        "leave_id": leave.id,
        "action": "approve",
        "reviewed_by": "Owner"
    })
    assert res_action.status_code == 200
    assert res_action.json()["status"] == "approved"

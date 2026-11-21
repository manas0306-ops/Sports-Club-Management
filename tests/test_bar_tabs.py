"""
Unit & Integration Tests for Bar, Running Tabs, KOT & Closing (Scene 4)
"""
from app.models.bar import BarTable, BarMenuItem, BarTab
from app.models.member import Member

def test_bar_running_tab_and_auto_discount(client, db_session):
    table = db_session.query(BarTable).first()
    gold_member = db_session.query(Member).filter(Member.tier == "gold").first()
    menu_item = db_session.query(BarMenuItem).first() # 200 price

    # 1. Open Running Tab for Gold Member
    res_open = client.post("/api/v1/bar/tabs/open", json={
        "table_id": table.id,
        "member_id": gold_member.id
    })
    assert res_open.status_code == 200
    tab_data = res_open.json()
    tab_id = tab_data["tab_id"]
    assert tab_data["discount_percent"] == 20.0 # Gold 20% discount applied automatically!

    # 2. Add 2 Protein Shakes -> Generates KOT ticket to kitchen
    res_add = client.post("/api/v1/bar/tabs/add-items", json={
        "tab_id": tab_id,
        "items": [{"menu_item_id": menu_item.id, "quantity": 2, "notes": "Extra cold"}]
    })
    assert res_add.status_code == 200
    data = res_add.json()
    # 400 gross - 20% auto discount (80) = 320 net + 5% F&B GST (16) = 336
    assert data["discount_amount"] == 80.0
    assert data["tax_amount"] == 16.0
    assert data["total_amount"] == 336.0

    # 3. Check Kitchen Display Ticket exists
    res_kot = client.get("/api/v1/bar/kitchen/tickets")
    assert res_kot.status_code == 200
    kot_tickets = res_kot.json()
    assert len(kot_tickets) >= 1
    assert kot_tickets[0]["table"] == table.table_number

    # 4. Settle Tab via UPI
    res_settle = client.post("/api/v1/bar/tabs/settle", json={
        "tab_id": tab_id,
        "payment_method": "upi"
    })
    assert res_settle.status_code == 200
    assert res_settle.json()["payment_method"] == "upi"

    # Verify table freed
    db_session.refresh(table)
    assert table.status == "available"

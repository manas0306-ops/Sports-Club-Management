"""
Unit & Integration Tests for Pro Shop & Unified Inventory (Scene 3)
Verifies: 'What a member buys at the counter and what they order from their sofa come from the same shelf.'
"""
from app.models.shop import Product
from app.models.member import Member

def test_unified_stock_counter_and_sofa_orders(client, db_session):
    product = db_session.query(Product).first()
    initial_stock = product.stock_quantity # 10 units
    gold_member = db_session.query(Member).filter(Member.tier == "gold").first()

    # 1. Counter POS Quick Sale: Member's string snapped 10 mins before match -> Buys 2 units at counter
    res_pos = client.post("/api/v1/shop/sale", json={
        "items": [{"product_id": product.id, "quantity": 2}],
        "channel": "counter_pos",
        "member_id": gold_member.id,
        "payment_method": "cash"
    })
    assert res_pos.status_code == 200
    db_session.refresh(product)
    assert product.stock_quantity == initial_stock - 2 # 8 left

    # 2. Online Sofa Order: Another member orders 3 units from home for Click & Collect
    res_web = client.post("/api/v1/shop/sale", json={
        "items": [{"product_id": product.id, "quantity": 3}],
        "channel": "online_click_collect",
        "customer_name": "Sofa Customer",
        "payment_method": "upi"
    })
    assert res_web.status_code == 200
    db_session.refresh(product)
    # MUST BE EXACT SAME SHELF: 8 - 3 = 5
    assert product.stock_quantity == 5

def test_gold_member_20_percent_shop_discount(client, db_session):
    product = db_session.query(Product).first() # 600 retail
    gold_member = db_session.query(Member).filter(Member.tier == "gold").first()

    res = client.post("/api/v1/shop/sale", json={
        "items": [{"product_id": product.id, "quantity": 1}],
        "member_id": gold_member.id
    })
    assert res.status_code == 200
    data = res.json()
    # 600 - 20% (120) = 480 subtotal + 12% GST (57.6) = 537.6
    assert data["subtotal"] == 480.0
    assert data["discount_amount"] == 120.0
    assert data["total_amount"] == 537.6

def test_insufficient_stock_rejection(client, db_session):
    product = db_session.query(Product).first()
    
    # Request more than available
    res = client.post("/api/v1/shop/sale", json={
        "items": [{"product_id": product.id, "quantity": product.stock_quantity + 50}]
    })
    assert res.status_code == 400
    assert "insufficient stock" in res.json()["detail"].lower()

"""
Unit & Integration Tests for Court Booking Domain (Scene 2)
Verifies: 1-hour sessions, 30-min slots, anti-collision, 2/day limit, tier pricing, Friday social play.
"""
from datetime import datetime, date, timedelta
from app.models.court import Court
from app.models.member import Member

def test_gold_member_court_booking_free(client, db_session):
    court = db_session.query(Court).first()
    gold_member = db_session.query(Member).filter(Member.tier == "gold").first()
    
    start_time = datetime.combine(date.today(), datetime.min.time()) + timedelta(hours=18) # 18:00
    payload = {
        "court_id": court.id,
        "member_id": gold_member.id,
        "start_time": start_time.isoformat(),
        "is_social_play": False
    }

    response = client.post("/api/v1/courts/book", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total_amount"] == 0.0 # 100% Free for Gold
    assert data["payment_status"] == "complimentary"

def test_anti_double_booking_prevention(client, db_session):
    """
    CRITICAL CONSTRAINT: 'Through all of it, two people must never end up on the same court at the same time.'
    """
    court = db_session.query(Court).first()
    gold_member = db_session.query(Member).filter(Member.tier == "gold").first()
    silver_member = db_session.query(Member).filter(Member.tier == "silver").first()

    start_time = datetime.combine(date.today() + timedelta(days=1), datetime.min.time()) + timedelta(hours=10) # 10:00

    # First booking
    res1 = client.post("/api/v1/courts/book", json={
        "court_id": court.id,
        "member_id": gold_member.id,
        "start_time": start_time.isoformat()
    })
    assert res1.status_code == 200

    # Overlapping booking 30 minutes later (10:30 on same court) -> Must FAIL with 409 Conflict
    overlap_time = start_time + timedelta(minutes=30)
    res2 = client.post("/api/v1/courts/book", json={
        "court_id": court.id,
        "member_id": silver_member.id,
        "start_time": overlap_time.isoformat()
    })
    assert res2.status_code == 409
    assert "already booked" in res2.json()["detail"].lower()

def test_max_two_bookings_per_member_per_day_limit(client, db_session):
    """
    CRITICAL CONSTRAINT: 'each member can play at most twice a day'
    """
    court = db_session.query(Court).filter(Court.sport_type == "tennis").first()
    court2 = db_session.query(Court).filter(Court.sport_type == "cricket").first()
    silver_member = db_session.query(Member).filter(Member.tier == "silver").first()

    target_day = date.today() + timedelta(days=2)
    t1 = datetime.combine(target_day, datetime.min.time()) + timedelta(hours=8)  # 08:00
    t2 = datetime.combine(target_day, datetime.min.time()) + timedelta(hours=16) # 16:00
    t3 = datetime.combine(target_day, datetime.min.time()) + timedelta(hours=18) # 18:00

    # Booking 1: OK
    r1 = client.post("/api/v1/courts/book", json={"court_id": court.id, "member_id": silver_member.id, "start_time": t1.isoformat()})
    assert r1.status_code == 200

    # Booking 2: OK
    r2 = client.post("/api/v1/courts/book", json={"court_id": court2.id, "member_id": silver_member.id, "start_time": t2.isoformat()})
    assert r2.status_code == 200

    # Booking 3 on same day: MUST BE REJECTED!
    r3 = client.post("/api/v1/courts/book", json={"court_id": court.id, "member_id": silver_member.id, "start_time": t3.isoformat()})
    assert r3.status_code == 400
    assert "at most 2 times a day" in r3.json()["detail"] or "daily limit exceeded" in r3.json()["detail"].lower()

def test_silver_member_court_pricing(client, db_session):
    """
    Silver gets 50% discount on court hourly rate + 18% GST
    """
    court = db_session.query(Court).first() # Rate 800
    silver_member = db_session.query(Member).filter(Member.tier == "silver").first()

    start_time = datetime.combine(date.today() + timedelta(days=3), datetime.min.time()) + timedelta(hours=14)
    res = client.post("/api/v1/courts/book", json={
        "court_id": court.id,
        "member_id": silver_member.id,
        "start_time": start_time.isoformat()
    })
    assert res.status_code == 200
    data = res.json()
    assert data["discount_percent"] == 50.0
    assert data["discount_amount"] == 400.0
    # 400 fee + 18% tax (72) = 472
    assert data["tax_amount"] == 72.0
    assert data["total_amount"] == 472.0

def test_friday_social_play_allows_multi_players(client, db_session):
    """
    Friday night social play: multiple players share the court session.
    """
    court = db_session.query(Court).first()
    gold_member = db_session.query(Member).filter(Member.tier == "gold").first()
    silver_member = db_session.query(Member).filter(Member.tier == "silver").first()

    friday_time = datetime.combine(date.today() + timedelta(days=4), datetime.min.time()) + timedelta(hours=19) # 19:00

    # Player 1 joins social session
    r1 = client.post("/api/v1/courts/book", json={
        "court_id": court.id,
        "member_id": gold_member.id,
        "start_time": friday_time.isoformat(),
        "is_social_play": True
    })
    assert r1.status_code == 200

    # Player 2 joins SAME social session at SAME time -> ALLOWED (registered_players increments)
    r2 = client.post("/api/v1/courts/book", json={
        "court_id": court.id,
        "member_id": silver_member.id,
        "start_time": friday_time.isoformat(),
        "is_social_play": True
    })
    assert r2.status_code == 200

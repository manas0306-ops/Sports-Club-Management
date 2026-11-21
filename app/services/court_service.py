"""
Court Booking Business Logic & Anti-Collision Engine
"""
from datetime import datetime, date, timedelta, time
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException

from app.models.court import Court, CourtBooking
from app.models.member import Member
from app.config import settings

def generate_booking_reference(db: Session) -> str:
    today_str = datetime.now().strftime("%Y%m%d")
    count = db.query(CourtBooking).count() + 1
    return f"BK-{today_str}-{count:04d}"

def validate_and_create_booking(
    db: Session,
    court_id: int,
    start_time: datetime,
    member_id: Optional[int] = None,
    guest_name: Optional[str] = None,
    guest_phone: Optional[str] = None,
    guest_email: Optional[str] = None,
    is_social_play: bool = False,
    payment_method: str = "counter"
) -> CourtBooking:
    # 1. Fetch Court
    court = db.query(Court).filter(Court.id == court_id, Court.is_active == True).first()
    if not court:
        raise HTTPException(status_code=404, detail="Court not found or inactive")

    # 2. Enforce 1-hour session duration & 30-minute slot alignment
    end_time = start_time + timedelta(minutes=settings.SLOT_DURATION_MINUTES)
    if start_time.minute not in (0, 30) or start_time.second != 0:
        raise HTTPException(status_code=400, detail="Sessions must start on 30-minute intervals (e.g., :00 or :30).")

    # 3. Enforce operating hours (06:00 to 22:00)
    if start_time.hour < settings.CLUB_OPEN_HOUR or end_time.hour > settings.CLUB_CLOSE_HOUR or (end_time.hour == settings.CLUB_CLOSE_HOUR and end_time.minute > 0):
        raise HTTPException(status_code=400, detail=f"Bookings are only permitted between {settings.CLUB_OPEN_HOUR:02d}:00 and {settings.CLUB_CLOSE_HOUR:02d}:00.")

    booking_date = start_time.date()

    # 4. Enforce member daily limit: "each member can play at most twice a day"
    member = None
    if member_id:
        member = db.query(Member).filter(Member.id == member_id).first()
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        
        # Check active status
        if member.status != "active":
            raise HTTPException(status_code=400, detail=f"Member membership is {member.status}. Cannot book court.")

        daily_bookings_count = db.query(CourtBooking).filter(
            CourtBooking.member_id == member_id,
            CourtBooking.booking_date == booking_date,
            CourtBooking.booking_status != "cancelled"
        ).count()

        if daily_bookings_count >= settings.MAX_DAILY_BOOKINGS_PER_MEMBER:
            raise HTTPException(
                status_code=400,
                detail=f"Daily limit exceeded: Members can play at most {settings.MAX_DAILY_BOOKINGS_PER_MEMBER} times a day. You already have {daily_bookings_count} active bookings on {booking_date}."
            )
    else:
        # Walk-in guest requires name and phone
        if not guest_name or not guest_phone:
            raise HTTPException(status_code=400, detail="Walk-in bookings require a customer name and phone number.")

    # 5. HARD CONSTRAINT: "Through all of it, two people must never end up on the same court at the same time"
    # Overlap formula: (existing.start < new_end) AND (existing.end > new_start)
    overlapping_query = db.query(CourtBooking).filter(
        CourtBooking.court_id == court_id,
        CourtBooking.booking_status != "cancelled",
        CourtBooking.start_time < end_time,
        CourtBooking.end_time > start_time
    )

    if is_social_play:
        # Friday Social Play allows up to 8 players to register for the session
        social_session = overlapping_query.filter(CourtBooking.is_social_play == True).first()
        if social_session:
            if social_session.registered_players_count >= 8:
                raise HTTPException(status_code=400, detail="This Friday Social Play session is already at full capacity (8/8 players).")
            # Increment player count on existing social session
            social_session.registered_players_count += 1
            db.commit()
            db.refresh(social_session)
            return social_session
        else:
            # Check if there is an individual booking blocking this time
            if overlapping_query.first():
                raise HTTPException(status_code=400, detail="Court conflict: An individual booking already exists on this court at this time.")
    else:
        # Regular individual booking - strict collision prevention
        conflict = overlapping_query.first()
        if conflict:
            raise HTTPException(
                status_code=409,
                detail=f"Court conflict: {court.name} is already booked from {conflict.start_time.strftime('%H:%M')} to {conflict.end_time.strftime('%H:%M')}."
            )

    # 6. Pricing Calculation based on Member Tier
    base_rate = court.hourly_rate
    tier_code = member.tier if member else "walkin"
    tier_info = settings.TIERS.get(tier_code, settings.TIERS["walkin"])
    court_discount_pct = tier_info.get("court_discount", 0.0)
    
    discount_amount = round(base_rate * court_discount_pct, 2)
    final_court_fee = round(base_rate - discount_amount, 2)
    
    # 18% Tax/GST on court fee if fee > 0
    tax_amount = round(final_court_fee * settings.TAX_RATE_COURTS, 2) if final_court_fee > 0 else 0.0
    total_amount = round(final_court_fee + tax_amount, 2)
    
    payment_status = "complimentary" if total_amount == 0 else "paid"

    booking = CourtBooking(
        booking_reference=generate_booking_reference(db),
        court_id=court_id,
        member_id=member_id,
        guest_name=guest_name if not member else member.full_name,
        guest_phone=guest_phone if not member else member.phone,
        guest_email=guest_email if not member else member.email,
        booking_date=booking_date,
        start_time=start_time,
        end_time=end_time,
        duration_minutes=settings.SLOT_DURATION_MINUTES,
        is_social_play=is_social_play,
        max_players=8 if is_social_play else 1,
        registered_players_count=1,
        base_rate=base_rate,
        discount_percent=round(court_discount_pct * 100, 1),
        discount_amount=discount_amount,
        final_court_fee=final_court_fee,
        tax_amount=tax_amount,
        total_amount=total_amount,
        payment_status=payment_status,
        payment_method="complimentary" if total_amount == 0 else payment_method,
        booking_status="confirmed"
    )

    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking

def get_court_schedule(db: Session, target_date: date) -> List[Dict[str, Any]]:
    courts = db.query(Court).filter(Court.is_active == True).all()
    schedule_data = []

    for court in courts:
        bookings = db.query(CourtBooking).filter(
            CourtBooking.court_id == court.id,
            CourtBooking.booking_date == target_date,
            CourtBooking.booking_status != "cancelled"
        ).order_by(CourtBooking.start_time).all()

        # Build half-hour slots from open to close
        slots = []
        curr = datetime.combine(target_date, time(settings.CLUB_OPEN_HOUR, 0))
        end_limit = datetime.combine(target_date, time(settings.CLUB_CLOSE_HOUR, 0))

        while curr + timedelta(minutes=settings.SLOT_DURATION_MINUTES) <= end_limit:
            slot_end = curr + timedelta(minutes=settings.SLOT_DURATION_MINUTES)
            
            # Check if any booking occupies this slot
            occupying = next(
                (b for b in bookings if b.start_time < slot_end and b.end_time > curr),
                None
            )
            
            slots.append({
                "start_time": curr.strftime("%H:%M"),
                "end_time": slot_end.strftime("%H:%M"),
                "is_available": occupying is None,
                "booking_reference": occupying.booking_reference if occupying else None,
                "is_social_play": occupying.is_social_play if occupying else False,
                "booked_by": occupying.guest_name if occupying else None,
                "member_tier": occupying.member.tier if (occupying and occupying.member) else ("walkin" if occupying else None)
            })
            curr += timedelta(minutes=settings.SLOT_INTERVAL_MINUTES)

        schedule_data.append({
            "court_id": court.id,
            "court_name": court.name,
            "sport_type": court.sport_type,
            "surface_type": court.surface_type,
            "hourly_rate": court.hourly_rate,
            "slots": slots
        })

    return schedule_data

def cancel_booking(db: Session, booking_id: int) -> CourtBooking:
    booking = db.query(CourtBooking).filter(CourtBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    booking.booking_status = "cancelled"
    db.commit()
    db.refresh(booking)
    return booking

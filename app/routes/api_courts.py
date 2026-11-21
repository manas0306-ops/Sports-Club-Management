"""
Court Booking API Router
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime

from app.database import get_db
from app.models.court import Court
from app.schemas.all_schemas import BookingCreateSchema
from app.services import court_service

router = APIRouter(prefix="/courts", tags=["Courts"])

@router.get("/")
def list_courts(db: Session = Depends(get_db)):
    courts = db.query(Court).filter(Court.is_active == True).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "sport_type": c.sport_type,
            "surface_type": c.surface_type,
            "hourly_rate": c.hourly_rate,
            "has_floodlights": c.has_floodlights
        }
        for c in courts
    ]

@router.get("/schedule")
def get_schedule(date_str: Optional[str] = Query(None, alias="date"), db: Session = Depends(get_db)):
    target_date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else date.today()
    return court_service.get_court_schedule(db, target_date=target_date)

@router.post("/book")
def book_court(payload: BookingCreateSchema, db: Session = Depends(get_db)):
    booking = court_service.validate_and_create_booking(
        db=db,
        court_id=payload.court_id,
        start_time=payload.start_time,
        member_id=payload.member_id,
        guest_name=payload.guest_name,
        guest_phone=payload.guest_phone,
        guest_email=str(payload.guest_email) if payload.guest_email else None,
        is_social_play=payload.is_social_play,
        payment_method=payload.payment_method
    )
    return {
        "success": True,
        "message": f"Court booking confirmed: {booking.booking_reference}",
        "booking_reference": booking.booking_reference,
        "court_name": booking.court.name,
        "date": str(booking.booking_date),
        "time": f"{booking.start_time.strftime('%H:%M')} - {booking.end_time.strftime('%H:%M')}",
        "base_rate": booking.base_rate,
        "discount_percent": booking.discount_percent,
        "discount_amount": booking.discount_amount,
        "tax_amount": booking.tax_amount,
        "total_amount": booking.total_amount,
        "payment_status": booking.payment_status
    }

@router.post("/cancel/{booking_id}")
def cancel_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = court_service.cancel_booking(db, booking_id=booking_id)
    return {
        "success": True,
        "message": f"Booking {booking.booking_reference} cancelled successfully."
    }

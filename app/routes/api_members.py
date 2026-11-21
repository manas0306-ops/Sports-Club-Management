"""
Member API Router
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.schemas.all_schemas import MemberCreateSchema, MemberRenewSchema
from app.services import member_service

router = APIRouter(prefix="/members", tags=["Members"])

@router.get("/search")
def search_members(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    members = member_service.search_members(db, query=q)
    return [
        {
            "id": m.id,
            "member_code": m.member_code,
            "name": m.full_name,
            "email": m.email,
            "phone": m.phone,
            "tier": m.tier,
            "status": m.status,
            "expiry_date": str(m.expiry_date),
            "is_expired": m.is_expired
        }
        for m in members
    ]

@router.post("/")
def create_member(payload: MemberCreateSchema, db: Session = Depends(get_db)):
    member = member_service.create_member(
        db=db,
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        phone=payload.phone,
        tier=payload.tier,
        date_of_birth=payload.date_of_birth,
        emergency_contact_name=payload.emergency_contact_name,
        emergency_contact_phone=payload.emergency_contact_phone,
        duration_months=payload.duration_months,
        notes=payload.notes
    )
    return {
        "success": True,
        "message": f"Member {member.full_name} enrolled successfully in {member.tier.capitalize()} Tier",
        "member_id": member.id,
        "member_code": member.member_code
    }

@router.get("/{member_id}")
def get_member_profile(member_id: int, db: Session = Depends(get_db)):
    profile = member_service.get_member_profile(db, member_id=member_id)
    m = profile["member"]
    return {
        "id": m.id,
        "member_code": m.member_code,
        "name": m.full_name,
        "first_name": m.first_name,
        "last_name": m.last_name,
        "email": m.email,
        "phone": m.phone,
        "tier": m.tier,
        "status": m.status,
        "start_date": str(m.start_date),
        "expiry_date": str(m.expiry_date),
        "days_to_expiry": profile["days_to_expiry"],
        "is_expired": profile["is_expired"],
        "privileges": profile["privileges"],
        "stats": profile["stats"],
        "recent_bookings": [
            {
                "reference": b.booking_reference,
                "court": b.court.name,
                "date": str(b.booking_date),
                "time": f"{b.start_time.strftime('%H:%M')} - {b.end_time.strftime('%H:%M')}",
                "amount": b.total_amount,
                "status": b.booking_status
            }
            for b in profile["history"]["recent_bookings"]
        ],
        "open_tab": {
            "tab_id": profile["history"]["open_tab"].id,
            "tab_number": profile["history"]["open_tab"].tab_number,
            "amount": profile["history"]["open_tab"].total_amount
        } if profile["history"]["open_tab"] else None
    }

@router.post("/{member_id}/renew")
def renew_membership(member_id: int, payload: MemberRenewSchema, db: Session = Depends(get_db)):
    member = member_service.renew_membership(db, member_id=member_id, months=payload.duration_months)
    return {
        "success": True,
        "message": f"Membership renewed until {member.expiry_date}",
        "new_expiry": str(member.expiry_date)
    }

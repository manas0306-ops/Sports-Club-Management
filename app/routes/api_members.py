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
@router.get("/{member_id}/profile")
def get_member_profile(member_id: int, db: Session = Depends(get_db)):
    profile = member_service.get_member_profile(db, member_id=member_id)
    m = profile["member"]
    priv = dict(profile["privileges"])
    priv["court_discount_pct"] = int(priv.get("court_discount", 0) * 100)
    priv["shop_discount_pct"] = int(priv.get("shop_discount", 0) * 100)
    priv["bar_discount_pct"] = int(priv.get("bar_discount", 0) * 100)

    bookings_list = [
        {
            "reference": b.booking_reference,
            "booking_reference": b.booking_reference,
            "court": b.court.name,
            "court_name": b.court.name,
            "date": str(b.booking_date),
            "time": f"{b.start_time.strftime('%H:%M')} - {b.end_time.strftime('%H:%M')}",
            "start_time": b.start_time.strftime('%H:%M'),
            "end_time": b.end_time.strftime('%H:%M'),
            "amount": b.total_amount,
            "amount_paid": b.total_amount,
            "status": b.booking_status
        }
        for b in profile["history"]["recent_bookings"]
    ]

    open_tab_data = {
        "tab_id": profile["history"]["open_tab"].id,
        "tab_number": profile["history"]["open_tab"].tab_number,
        "table": f"Table #{profile['history']['open_tab'].table_id}",
        "amount": profile["history"]["open_tab"].total_amount,
        "total_bill": profile["history"]["open_tab"].total_amount
    } if profile["history"]["open_tab"] else None

    shop_orders_list = [
        {
            "order_number": o.order_number,
            "created_at": o.created_at.strftime('%Y-%m-%d %H:%M') if o.created_at else str(m.start_date),
            "channel": o.channel,
            "total_amount": o.total_amount
        }
        for o in profile["history"]["recent_shop_orders"]
    ]

    return {
        "id": m.id,
        "member_code": m.member_code,
        "name": m.full_name,
        "full_name": m.full_name,
        "first_name": m.first_name,
        "last_name": m.last_name,
        "photo_url": m.photo_url or f"https://api.dicebear.com/7.x/initials/svg?seed={m.first_name}+{m.last_name}",
        "email": m.email,
        "phone": m.phone,
        "tier": m.tier,
        "status": m.status,
        "start_date": str(m.start_date),
        "expiry_date": str(m.expiry_date),
        "days_to_expiry": profile["days_to_expiry"],
        "days_until_expiry": profile["days_to_expiry"],
        "is_expired": profile["is_expired"],
        "privileges": priv,
        "stats": profile["stats"],
        "total_club_spend": profile["stats"].get("total_spend", 0),
        "recent_bookings": bookings_list,
        "recent_court_bookings": bookings_list,
        "open_tab": open_tab_data,
        "open_bar_tab": open_tab_data,
        "recent_shop_orders": shop_orders_list
    }

@router.post("/{member_id}/renew")
def renew_membership(member_id: int, payload: Optional[MemberRenewSchema] = None, db: Session = Depends(get_db)):
    months = payload.duration_months if (payload and payload.duration_months) else 12
    member = member_service.renew_membership(db, member_id=member_id, months=months)
    return {
        "success": True,
        "message": f"Membership renewed until {member.expiry_date}",
        "new_expiry": str(member.expiry_date)
    }

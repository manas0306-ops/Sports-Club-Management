"""
Member Business Logic & Privileges Service
"""
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from fastapi import HTTPException

from app.models.member import Member, MemberTier, MemberStatus
from app.models.court import CourtBooking
from app.models.shop import ShopOrder
from app.models.bar import BarTab
from app.config import settings

def generate_member_code(db: Session, tier: str) -> str:
    count = db.query(Member).count() + 1
    prefix = tier.upper()[:3]
    return f"TC-{prefix}-{count:04d}"

def get_tier_privileges(tier: str) -> Dict[str, Any]:
    tier_lower = tier.lower()
    return settings.TIERS.get(tier_lower, settings.TIERS["walkin"])

def create_member(
    db: Session,
    first_name: str,
    last_name: str,
    email: str,
    phone: str,
    tier: str,
    date_of_birth: Optional[date] = None,
    emergency_contact_name: Optional[str] = None,
    emergency_contact_phone: Optional[str] = None,
    duration_months: int = 12,
    notes: Optional[str] = None,
    photo_url: Optional[str] = None
) -> Member:
    # Check existing email or phone
    existing = db.query(Member).filter(or_(Member.email == email, Member.phone == phone)).first()
    if existing:
        raise HTTPException(status_code=400, detail="A member with this email or phone number already exists.")
    
    tier_clean = tier.lower()
    if tier_clean not in settings.TIERS:
        raise HTTPException(status_code=400, detail=f"Invalid tier: {tier}. Choose from gold, silver, junior, walkin.")
    
    is_junior = False
    if date_of_birth:
        age = (date.today() - date_of_birth).days // 365
        if age < 18:
            is_junior = True
    if tier_clean == "junior" and not is_junior:
        # If explicitly enrolled in junior, mark as junior
        is_junior = True

    today = date.today()
    expiry = today + timedelta(days=duration_months * 30)
    member_code = generate_member_code(db, tier_clean)

    member = Member(
        member_code=member_code,
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        email=email.strip().lower(),
        phone=phone.strip(),
        date_of_birth=date_of_birth,
        is_junior=is_junior,
        tier=tier_clean,
        status=MemberStatus.ACTIVE.value,
        start_date=today,
        expiry_date=expiry,
        emergency_contact_name=emergency_contact_name,
        emergency_contact_phone=emergency_contact_phone,
        notes=notes,
        photo_url=photo_url or f"https://api.dicebear.com/7.x/initials/svg?seed={first_name}+{last_name}"
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member

def search_members(db: Session, query: str, limit: int = 20) -> List[Member]:
    q = f"%{query.strip()}%"
    return db.query(Member).filter(
        or_(
            Member.member_code.ilike(q),
            Member.first_name.ilike(q),
            Member.last_name.ilike(q),
            Member.email.ilike(q),
            Member.phone.ilike(q)
        )
    ).limit(limit).all()

def get_member_profile(db: Session, member_id: int) -> Dict[str, Any]:
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Check expiry status
    is_expired = member.expiry_date < date.today()
    if is_expired and member.status == MemberStatus.ACTIVE.value:
        member.status = MemberStatus.EXPIRED.value
        db.commit()

    privileges = get_tier_privileges(member.tier)
    
    # Fetch club history
    bookings = db.query(CourtBooking).filter(
        CourtBooking.member_id == member.id
    ).order_by(desc(CourtBooking.booking_date)).limit(10).all()
    
    orders = db.query(ShopOrder).filter(
        ShopOrder.member_id == member.id
    ).order_by(desc(ShopOrder.created_at)).limit(10).all()
    
    tabs = db.query(BarTab).filter(
        BarTab.member_id == member.id
    ).order_by(desc(BarTab.opened_at)).limit(10).all()
    
    total_court_spend = sum(b.total_amount for b in bookings if b.payment_status == "paid")
    total_shop_spend = sum(o.total_amount for o in orders if o.payment_status == "paid")
    total_bar_spend = sum(t.total_amount for t in tabs if t.status == "settled")
    
    open_tab = db.query(BarTab).filter(
        BarTab.member_id == member.id,
        BarTab.status == "open"
    ).first()

    return {
        "member": member,
        "is_expired": is_expired,
        "days_to_expiry": (member.expiry_date - date.today()).days,
        "privileges": privileges,
        "history": {
            "recent_bookings": bookings,
            "recent_shop_orders": orders,
            "recent_bar_tabs": tabs,
            "open_tab": open_tab
        },
        "stats": {
            "total_bookings_count": len(bookings),
            "total_spend": round(total_court_spend + total_shop_spend + total_bar_spend, 2),
            "court_spend": round(total_court_spend, 2),
            "shop_spend": round(total_shop_spend, 2),
            "bar_spend": round(total_bar_spend, 2)
        }
    }

def renew_membership(db: Session, member_id: int, months: int = 12) -> Member:
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    current_expiry = max(member.expiry_date, date.today())
    member.expiry_date = current_expiry + timedelta(days=months * 30)
    member.status = MemberStatus.ACTIVE.value
    db.commit()
    db.refresh(member)
    return member

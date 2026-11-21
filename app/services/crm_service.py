"""
CRM, Online Enquiries, Trial Bookings & Quote Generator Service
"""
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException

from app.models.crm import LeadEnquiry, TrialBooking, Quote
from app.models.member import Member
from app.services.member_service import create_member
from app.config import settings

def generate_enquiry_number(db: Session) -> str:
    count = db.query(LeadEnquiry).count() + 1
    return f"LEAD-{datetime.now().strftime('%Y%m')}-{count:04d}"

def generate_quote_number(db: Session) -> str:
    count = db.query(Quote).count() + 1
    return f"QT-{datetime.now().strftime('%Y%m')}-{count:04d}"

def capture_lead_enquiry(
    db: Session,
    name: str,
    email: str,
    phone: str,
    interested_sport: str = "tennis",
    interested_tier: str = "gold",
    notes: Optional[str] = None,
    source: str = "website_form"
) -> LeadEnquiry:
    lead = LeadEnquiry(
        enquiry_number=generate_enquiry_number(db),
        name=name.strip(),
        email=email.strip().lower(),
        phone=phone.strip(),
        interested_sport=interested_sport,
        interested_tier=interested_tier,
        source=source,
        status="new",
        notes=notes,
        follow_up_date=date.today() + timedelta(days=1)
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead

def book_trial_session(
    db: Session,
    visitor_name: str,
    visitor_email: str,
    visitor_phone: str,
    sport_type: str,
    trial_date: date,
    trial_time_slot: str,
    lead_id: Optional[int] = None
) -> TrialBooking:
    # If no lead_id, create or find lead
    if not lead_id:
        existing_lead = db.query(LeadEnquiry).filter(LeadEnquiry.email == visitor_email.lower()).first()
        if existing_lead:
            lead_id = existing_lead.id
            existing_lead.status = "trial_scheduled"
        else:
            new_lead = capture_lead_enquiry(
                db=db,
                name=visitor_name,
                email=visitor_email,
                phone=visitor_phone,
                interested_sport=sport_type,
                source="trial_booking_widget"
            )
            new_lead.status = "trial_scheduled"
            lead_id = new_lead.id
    else:
        lead = db.query(LeadEnquiry).filter(LeadEnquiry.id == lead_id).first()
        if lead:
            lead.status = "trial_scheduled"

    trial_ref = f"TRL-{datetime.now().strftime('%Y%m%d')}-{db.query(TrialBooking).count() + 1:04d}"
    trial = TrialBooking(
        trial_reference=trial_ref,
        lead_id=lead_id,
        visitor_name=visitor_name,
        visitor_email=visitor_email,
        visitor_phone=visitor_phone,
        sport_type=sport_type,
        trial_date=trial_date,
        trial_time_slot=trial_time_slot,
        assigned_coach="Coach David (Head Pro)",
        status="scheduled"
    )
    db.add(trial)
    db.commit()
    db.refresh(trial)
    return trial

def generate_membership_quote(
    db: Session,
    lead_id: int,
    tier_proposed: str,
    coaching_addon_fee: float = 0.0,
    discount_amount: float = 0.0
) -> Quote:
    lead = db.query(LeadEnquiry).filter(LeadEnquiry.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    tier_info = settings.TIERS.get(tier_proposed.lower(), settings.TIERS["silver"])
    membership_fee = tier_info.get("monthly_fee", 2500.0) * 12 # Annual quote
    
    subtotal = membership_fee + coaching_addon_fee - discount_amount
    tax = round(subtotal * 0.18, 2) # 18% GST
    total = round(subtotal + tax, 2)

    quote = Quote(
        quote_number=generate_quote_number(db),
        lead_id=lead.id,
        customer_name=lead.name,
        customer_email=lead.email,
        plan_tier=tier_proposed,
        membership_fee=membership_fee,
        coaching_addon_fee=coaching_addon_fee,
        discount_amount=discount_amount,
        tax_amount=tax,
        total_quote_amount=total,
        valid_until=date.today() + timedelta(days=14),
        terms="Annual membership package with full club privileges. Rate locked for 14 days.",
        status="sent"
    )
    
    lead.status = "quote_sent"
    db.add(quote)
    db.commit()
    db.refresh(quote)
    return quote

def convert_lead_to_member(
    db: Session,
    lead_id: int,
    tier: str,
    emergency_contact_name: Optional[str] = None,
    emergency_contact_phone: Optional[str] = None
) -> Member:
    lead = db.query(LeadEnquiry).filter(LeadEnquiry.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Name split
    parts = lead.name.split(" ", 1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else "Member"

    # Create member
    member = create_member(
        db=db,
        first_name=first_name,
        last_name=last_name,
        email=lead.email,
        phone=lead.phone,
        tier=tier,
        emergency_contact_name=emergency_contact_name,
        emergency_contact_phone=emergency_contact_phone,
        notes=f"Converted from Lead #{lead.enquiry_number} ({lead.source})"
    )

    lead.status = "converted"
    lead.converted_member_id = member.id
    db.commit()
    return member

def get_crm_pipeline(db: Session) -> Dict[str, List[Any]]:
    leads = db.query(LeadEnquiry).order_by(desc(LeadEnquiry.created_at)).all()
    pipeline = {
        "new": [],
        "contacted": [],
        "trial_scheduled": [],
        "quote_sent": [],
        "converted": [],
        "lost": []
    }
    for l in leads:
        st = l.status if l.status in pipeline else "new"
        pipeline[st].append({
            "id": l.id,
            "enquiry_number": l.enquiry_number,
            "name": l.name,
            "email": l.email,
            "phone": l.phone,
            "sport": l.interested_sport,
            "tier": l.interested_tier,
            "source": l.source,
            "status": l.status,
            "notes": l.notes,
            "follow_up_date": str(l.follow_up_date) if l.follow_up_date else None,
            "created_at": l.created_at.strftime("%Y-%m-%d %H:%M")
        })
    return pipeline

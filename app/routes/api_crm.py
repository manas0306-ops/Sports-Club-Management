"""
CRM, Leads, Website Enquiries & Quotes API Router
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.all_schemas import (
    LeadCreateSchema, TrialBookingSchema, QuoteCreateSchema, ConvertLeadSchema
)
from app.services import crm_service

router = APIRouter(prefix="/crm", tags=["CRM & Website Enquiries"])

@router.get("/pipeline")
def get_pipeline(db: Session = Depends(get_db)):
    return crm_service.get_crm_pipeline(db)

@router.post("/enquiries")
def create_enquiry(payload: LeadCreateSchema, db: Session = Depends(get_db)):
    lead = crm_service.capture_lead_enquiry(
        db=db,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        interested_sport=payload.interested_sport,
        interested_tier=payload.interested_tier,
        notes=payload.notes,
        source=payload.source
    )
    return {
        "success": True,
        "message": "Thank you for contacting The Champions Club! Our team will reach out shortly.",
        "enquiry_number": lead.enquiry_number,
        "lead_id": lead.id
    }

@router.post("/trials")
def book_trial(payload: TrialBookingSchema, db: Session = Depends(get_db)):
    trial = crm_service.book_trial_session(
        db=db,
        visitor_name=payload.visitor_name,
        visitor_email=payload.visitor_email,
        visitor_phone=payload.visitor_phone,
        sport_type=payload.sport_type,
        trial_date=payload.trial_date,
        trial_time_slot=payload.trial_time_slot,
        lead_id=payload.lead_id
    )
    return {
        "success": True,
        "message": f"Trial session confirmed for {trial.visitor_name} with {trial.assigned_coach}!",
        "trial_reference": trial.trial_reference,
        "date": str(trial.trial_date),
        "slot": trial.trial_time_slot
    }

@router.post("/quotes")
def generate_quote(payload: QuoteCreateSchema, db: Session = Depends(get_db)):
    quote = crm_service.generate_membership_quote(
        db=db,
        lead_id=payload.lead_id,
        tier_proposed=payload.tier_proposed,
        coaching_addon_fee=payload.coaching_addon_fee,
        discount_amount=payload.discount_amount
    )
    return {
        "success": True,
        "message": f"Quote {quote.quote_number} generated for {quote.customer_name}.",
        "quote_number": quote.quote_number,
        "plan_tier": quote.plan_tier,
        "total_quote_amount": quote.total_quote_amount,
        "valid_until": str(quote.valid_until)
    }

@router.post("/convert")
def convert_lead(payload: ConvertLeadSchema, db: Session = Depends(get_db)):
    member = crm_service.convert_lead_to_member(
        db=db,
        lead_id=payload.lead_id,
        tier=payload.tier,
        emergency_contact_name=payload.emergency_contact_name,
        emergency_contact_phone=payload.emergency_contact_phone
    )
    return {
        "success": True,
        "message": f"Successfully converted lead into active {member.tier.capitalize()} member!",
        "member_id": member.id,
        "member_code": member.member_code,
        "member_name": member.full_name
    }

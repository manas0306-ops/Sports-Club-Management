"""
CRM, Leads & Trial Booking Models
"""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base

class LeadEnquiry(Base):
    __tablename__ = "lead_enquiries"

    id = Column(Integer, primary_key=True, index=True)
    enquiry_number = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(150), index=True, nullable=False)
    phone = Column(String(30), nullable=False)
    
    interested_sport = Column(String(50), default="tennis") # tennis, cricket, padel, multiple
    interested_tier = Column(String(20), default="gold") # gold, silver, junior
    source = Column(String(50), default="website_form") # website_form, phone, walkin, social_media
    
    status = Column(String(30), default="new") # new, contacted, trial_scheduled, quote_sent, converted, lost
    notes = Column(Text, nullable=True)
    follow_up_date = Column(Date, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    converted_member_id = Column(Integer, ForeignKey("members.id"), nullable=True)

    quotes = relationship("Quote", back_populates="lead", cascade="all, delete-orphan")
    trial_bookings = relationship("TrialBooking", back_populates="lead", cascade="all, delete-orphan")

class TrialBooking(Base):
    __tablename__ = "trial_bookings"

    id = Column(Integer, primary_key=True, index=True)
    trial_reference = Column(String(50), unique=True, index=True, nullable=False)
    lead_id = Column(Integer, ForeignKey("lead_enquiries.id"), nullable=True)
    
    visitor_name = Column(String(100), nullable=False)
    visitor_email = Column(String(150), nullable=False)
    visitor_phone = Column(String(30), nullable=False)
    
    sport_type = Column(String(50), default="tennis")
    trial_date = Column(Date, nullable=False)
    trial_time_slot = Column(String(30), nullable=False) # e.g. "17:00 - 18:00"
    
    assigned_coach = Column(String(100), default="Coach David")
    status = Column(String(30), default="scheduled") # scheduled, completed, cancelled, converted
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    lead = relationship("LeadEnquiry", back_populates="trial_bookings")

class Quote(Base):
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, index=True)
    quote_number = Column(String(50), unique=True, index=True, nullable=False)
    lead_id = Column(Integer, ForeignKey("lead_enquiries.id"), nullable=False)
    
    customer_name = Column(String(100), nullable=False)
    customer_email = Column(String(150), nullable=False)
    plan_tier = Column(String(20), nullable=False)
    
    membership_fee = Column(Float, nullable=False)
    coaching_addon_fee = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    total_quote_amount = Column(Float, nullable=False)
    
    valid_until = Column(Date, nullable=False)
    terms = Column(Text, nullable=True)
    status = Column(String(20), default="sent") # draft, sent, accepted, declined
    created_at = Column(DateTime, default=datetime.utcnow)

    lead = relationship("LeadEnquiry", back_populates="quotes")

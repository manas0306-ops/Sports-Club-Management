"""
Court & CourtBooking Models
"""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base

class Court(Base):
    __tablename__ = "courts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False) # "Tennis Court 1 (Centre)", "Cricket Net A"
    sport_type = Column(String(50), nullable=False) # "tennis", "cricket", "padel", "badminton"
    surface_type = Column(String(50), default="synthetic") # "clay", "grass", "synthetic", "turf"
    has_floodlights = Column(Boolean, default=True)
    hourly_rate = Column(Float, default=800.0) # Base rate for walk-ins
    is_active = Column(Boolean, default=True)
    description = Column(Text, nullable=True)

    bookings = relationship("CourtBooking", back_populates="court", cascade="all, delete-orphan")

class CourtBooking(Base):
    __tablename__ = "court_bookings"

    id = Column(Integer, primary_key=True, index=True)
    booking_reference = Column(String(50), unique=True, index=True, nullable=False)
    
    court_id = Column(Integer, ForeignKey("courts.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=True) # Null if walk-in guest
    
    guest_name = Column(String(100), nullable=True)
    guest_phone = Column(String(30), nullable=True)
    guest_email = Column(String(150), nullable=True)
    
    booking_date = Column(Date, index=True, nullable=False)
    start_time = Column(DateTime, index=True, nullable=False)
    end_time = Column(DateTime, index=True, nullable=False)
    duration_minutes = Column(Integer, default=60) # 1 hour sessions
    
    # Friday Social Play support
    is_social_play = Column(Boolean, default=False)
    max_players = Column(Integer, default=1) # 1 for individual session, 8 for social play
    registered_players_count = Column(Integer, default=1)
    
    # Financial breakdown
    base_rate = Column(Float, default=800.0)
    discount_percent = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    final_court_fee = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    
    payment_status = Column(String(20), default="unpaid") # paid, unpaid, complimentary
    payment_method = Column(String(20), default="counter") # cash, card, upi, online, complimentary
    booking_status = Column(String(20), default="confirmed") # confirmed, cancelled, completed
    
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    court = relationship("Court", back_populates="bookings")
    member = relationship("Member", back_populates="court_bookings")

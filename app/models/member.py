"""
Member & Tier Domain Models
"""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, Text, Enum
from sqlalchemy.orm import relationship
import enum

from app.database import Base

class MemberTier(str, enum.Enum):
    GOLD = "gold"
    SILVER = "silver"
    JUNIOR = "junior"
    WALKIN = "walkin"

class MemberStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    PENDING = "pending"
    SUSPENDED = "suspended"

class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    member_code = Column(String(50), unique=True, index=True, nullable=False) # e.g. TC-GOLD-001
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    phone = Column(String(30), unique=True, index=True, nullable=False)
    date_of_birth = Column(Date, nullable=True)
    is_junior = Column(Boolean, default=False)
    
    tier = Column(String(20), default="silver", nullable=False) # gold, silver, junior, walkin
    status = Column(String(20), default="active", nullable=False) # active, expired, pending
    
    start_date = Column(Date, default=date.today)
    expiry_date = Column(Date, nullable=False)
    
    emergency_contact_name = Column(String(100), nullable=True)
    emergency_contact_phone = Column(String(30), nullable=True)
    notes = Column(Text, nullable=True)
    photo_url = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    court_bookings = relationship("CourtBooking", back_populates="member", cascade="all, delete-orphan")
    shop_orders = relationship("ShopOrder", back_populates="member")
    bar_tabs = relationship("BarTab", back_populates="member")
    invoices = relationship("Invoice", back_populates="member")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def is_expired(self) -> bool:
        if not self.expiry_date:
            return False
        return self.expiry_date < date.today()

    @property
    def days_to_expiry(self) -> int:
        if not self.expiry_date:
            return 999
        return (self.expiry_date - date.today()).days

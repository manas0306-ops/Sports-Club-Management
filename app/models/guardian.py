"""
Guardian Model for Underage Members
"""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base

class Guardian(Base):
    __tablename__ = "guardians"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), unique=True, nullable=False)
    
    guardian_name = Column(String(120), nullable=False)
    relationship_type = Column(String(50), default="Parent") # Parent, Legal Guardian, Coach
    contact_phone = Column(String(30), nullable=False)
    contact_email = Column(String(150), nullable=True)
    
    consent_status = Column(String(30), default="approved") # approved, pending, revoked
    consent_date = Column(Date, default=date.today)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    member = relationship("Member", back_populates="guardian")

    def __repr__(self):
        return f"<Guardian for Member {self.member_id}: {self.guardian_name} ({self.consent_status})>"

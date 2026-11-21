"""
User Account Model & Primary Roles
"""
from datetime import datetime
import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship

from app.database import Base

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"
    PLAYER = "PLAYER"
    STAFF = "STAFF"
    WALK_IN = "WALK_IN"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(150), unique=True, index=True, nullable=False)
    username = Column(String(80), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    primary_role = Column(String(20), default=UserRole.MEMBER.value, nullable=False)
    
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Linked Profiles
    member_profile = relationship("Member", back_populates="user", uselist=False)
    player_profile = relationship("PlayerProfile", back_populates="user", uselist=False)
    employee_profile = relationship("Employee", back_populates="user", uselist=False)

    def __repr__(self):
        return f"<User id={self.id} username='{self.username}' role='{self.primary_role}'>"

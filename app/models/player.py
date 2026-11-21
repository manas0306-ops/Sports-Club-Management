"""
Player Athlete Profile Model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base

class PlayerProfile(Base):
    __tablename__ = "player_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    athlete_name = Column(String(120), nullable=False)
    email = Column(String(150), nullable=False)
    phone = Column(String(30), nullable=False)
    
    primary_sport = Column(String(50), default="Tennis") # Tennis, Cricket, Padel, Badminton
    secondary_sports = Column(String(100), default="Padel, Badminton")
    skill_level = Column(String(30), default="Advanced") # Beginner, Intermediate, Advanced, Professional
    club_ranking = Column(String(50), default="Club Rank #4")
    team_name = Column(String(100), default="The Champions Elite Squad")
    
    training_schedule = Column(Text, nullable=True) # JSON or formatted string
    upcoming_matches = Column(Text, nullable=True) # JSON or formatted string
    match_history = Column(Text, nullable=True) # JSON or formatted string
    performance_metrics = Column(Text, nullable=True) # JSON or formatted string
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="player_profile")

    def __repr__(self):
        return f"<PlayerProfile id={self.id} athlete='{self.athlete_name}' sport='{self.primary_sport}'>"

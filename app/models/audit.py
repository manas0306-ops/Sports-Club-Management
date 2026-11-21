"""
System Activity and Security Audit Log Model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text

from app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    username = Column(String(80), nullable=True)
    action = Column(String(100), nullable=False) # LOGIN_SUCCESS, LOGIN_FAILURE, ROLE_MISMATCH, UNAUTHORIZED_ACCESS, RENEWAL
    resource = Column(String(150), nullable=True) # /admin/dashboard, /api/v1/finance, etc.
    ip_address = Column(String(50), nullable=True)
    status = Column(String(30), default="SUCCESS") # SUCCESS, FAILED, FORBIDDEN
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<AuditLog id={self.id} action='{self.action}' status='{self.status}'>"

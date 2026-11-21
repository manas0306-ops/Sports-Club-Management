"""
Owner Financials, Invoicing, HR, Shifts & Leave Models
"""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), unique=True, index=True, nullable=False) # e.g. INV-2026-0045
    invoice_type = Column(String(50), default="member_dues") # member_dues, corporate_client, tournament_booking
    
    member_id = Column(Integer, ForeignKey("members.id"), nullable=True)
    client_name = Column(String(150), nullable=False)
    client_email = Column(String(150), nullable=False)
    client_tax_id = Column(String(50), nullable=True) # GSTIN / Corporate ID
    client_address = Column(Text, nullable=True)
    
    issue_date = Column(Date, default=date.today)
    due_date = Column(Date, nullable=False)
    
    subtotal = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    amount_paid = Column(Float, default=0.0)
    
    status = Column(String(20), default="sent") # draft, sent, paid, overdue, cancelled
    payment_method = Column(String(30), nullable=True)
    notes = Column(Text, nullable=True)
    line_items_summary = Column(Text, nullable=True) # JSON or descriptive string
    
    created_at = Column(DateTime, default=datetime.utcnow)

    member = relationship("Member", back_populates="invoices")

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    employee_code = Column(String(50), unique=True, nullable=False) # e.g. EMP-001
    name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False) # "front_desk", "bartender", "head_coach", "maintenance", "manager"
    email = Column(String(150), unique=True, nullable=False)
    phone = Column(String(30), nullable=False)
    
    monthly_salary = Column(Float, default=30000.0)
    hourly_rate = Column(Float, default=200.0)
    hire_date = Column(Date, default=date.today)
    is_active = Column(Boolean, default=True)

    shifts = relationship("StaffShift", back_populates="employee", cascade="all, delete-orphan")
    leaves = relationship("LeaveRequest", back_populates="employee", cascade="all, delete-orphan")

class StaffShift(Base):
    __tablename__ = "staff_shifts"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    shift_date = Column(Date, nullable=False)
    start_time = Column(String(20), nullable=False) # e.g. "08:00"
    end_time = Column(String(20), nullable=False) # e.g. "16:00"
    department = Column(String(50), default="front_desk") # front_desk, bar_kitchen, courts, maintenance
    status = Column(String(20), default="scheduled") # scheduled, completed, missed

    employee = relationship("Employee", back_populates="shifts")

class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    leave_type = Column(String(50), default="casual") # casual, sick, annual
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    total_days = Column(Integer, default=1)
    reason = Column(Text, nullable=False)
    
    status = Column(String(20), default="pending") # pending, approved, rejected
    reviewed_by = Column(String(100), nullable=True)
    review_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="leaves")

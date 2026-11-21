"""
Bar, Cafeteria, Table Tracking & Kitchen Order Ticket (KOT) Models
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base

class BarTable(Base):
    __tablename__ = "bar_tables"

    id = Column(Integer, primary_key=True, index=True)
    table_number = Column(String(20), unique=True, nullable=False) # e.g. "T-01", "Bar-03", "Patio-02"
    area = Column(String(50), default="main_hall") # "main_hall", "lounge", "terrace", "bar_counter"
    capacity = Column(Integer, default=4)
    status = Column(String(20), default="available") # "available", "occupied", "reserved"

    tabs = relationship("BarTab", back_populates="table")

class BarMenuItem(Base):
    __tablename__ = "bar_menu_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False) # "drinks_beers", "mocktails", "shakes", "meals", "snacks"
    price = Column(Float, nullable=False)
    is_kitchen_item = Column(Boolean, default=True) # Sends KOT to kitchen if True
    is_available = Column(Boolean, default=True)
    description = Column(Text, nullable=True)

class BarTab(Base):
    __tablename__ = "bar_tabs"

    id = Column(Integer, primary_key=True, index=True)
    tab_number = Column(String(50), unique=True, index=True, nullable=False) # e.g. TAB-20261121-001
    table_id = Column(Integer, ForeignKey("bar_tables.id"), nullable=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=True)
    
    customer_name = Column(String(100), nullable=False)
    customer_phone = Column(String(30), nullable=True)
    
    status = Column(String(20), default="open") # "open", "settled", "void"
    opened_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    
    subtotal = Column(Float, default=0.0)
    discount_percent = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    tip_amount = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    
    payment_method = Column(String(30), nullable=True) # "cash", "card", "upi", "split"
    server_staff_name = Column(String(100), default="Bar Staff")

    table = relationship("BarTable", back_populates="tabs")
    member = relationship("Member", back_populates="bar_tabs")
    items = relationship("BarOrderItem", back_populates="tab", cascade="all, delete-orphan")

class BarOrderItem(Base):
    __tablename__ = "bar_order_items"

    id = Column(Integer, primary_key=True, index=True)
    tab_id = Column(Integer, ForeignKey("bar_tabs.id"), nullable=False)
    menu_item_id = Column(Integer, ForeignKey("bar_menu_items.id"), nullable=False)
    item_name = Column(String(100), nullable=False)
    
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    
    # Kitchen Order Ticket (KOT) Tracking
    kot_ticket_number = Column(String(50), index=True, nullable=False)
    kitchen_notes = Column(String(200), nullable=True) # e.g. "Less spice", "No ice"
    kot_status = Column(String(20), default="pending") # "pending", "preparing", "ready", "served"
    ordered_at = Column(DateTime, default=datetime.utcnow)

    tab = relationship("BarTab", back_populates="items")
    menu_item = relationship("BarMenuItem")

class BarDailyClosing(Base):
    __tablename__ = "bar_daily_closings"

    id = Column(Integer, primary_key=True, index=True)
    closing_date = Column(DateTime, default=datetime.utcnow)
    closed_by_staff = Column(String(100), default="Head Bartender")
    
    total_sales = Column(Float, default=0.0)
    total_cash = Column(Float, default=0.0)
    total_card = Column(Float, default=0.0)
    total_upi = Column(Float, default=0.0)
    tax_total = Column(Float, default=0.0)
    tabs_settled_count = Column(Integer, default=0)
    open_tabs_count = Column(Integer, default=0)
    notes = Column(Text, nullable=True)

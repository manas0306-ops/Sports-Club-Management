from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Date, Boolean, ForeignKey, JSON
from database import Base

def key(): return Column(Integer, primary_key=True)
def fk(table, nullable=False): return Column(Integer, ForeignKey(table + ".id"), nullable=nullable, index=True)
def word(default=""): return Column(String, nullable=False, default=default)
def number(default=0): return Column(Integer, nullable=False, default=default)
def stamp(): return Column(DateTime, default=datetime.now, nullable=False, index=True)

class User(Base):
    __tablename__ = "users"
    id=key(); email=Column(String, unique=True, nullable=False); name=word(); password=word(); role=word("member")
    active=Column(Boolean, default=True); sessions=Column(JSON, default=list); shifts=Column(JSON, default=list)

class Member(Base):
    __tablename__="members"
    id=key(); user_id=Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    dob=Column(Date, nullable=False); tier=word("Free"); expiry=Column(Date)

class Court(Base):
    __tablename__="courts"
    id=key(); name=word(); sport=word(); kind=word(); price=number(); social=Column(Boolean,default=False)

class Booking(Base):
    __tablename__="court_bookings"
    id=key(); court_id=fk("courts"); member_id=fk("members"); start=Column(DateTime,index=True); end=Column(DateTime)
    is_social=Column(Boolean,default=False); status=word("Booked"); sale_id=fk("sales",True)

class Product(Base):
    __tablename__="products"
    id=key(); name=word(); department=word(); category=word(); price=number(); cost=number()
    stock_on_hand=number(); reorder_level=number(3)

class Sale(Base):
    __tablename__="sales"
    id=key(); member_id=fk("members",True); actor_id=fk("users"); shift_id=fk("bar_shifts",True)
    department=word(); mode=word(); status=word("Paid"); total=number(); cost=number(); discount=number()
    tax=number(); details=Column(JSON,default=dict); created=stamp(); settled=Column(DateTime,index=True)

class Item(Base):
    __tablename__="sale_items"
    id=key(); sale_id=fk("sales"); product_id=fk("products",True); name=word(); qty=number(1)
    price=number(); discount=number(); total=number(); ticket=word(); batch=number()

class Appointment(Base):
    __tablename__="physio_appointments"
    id=key(); member_id=fk("members"); staff_id=fk("users"); start=Column(DateTime,index=True)
    status=word("Booked"); summary=word(); sale_id=fk("sales",True)

class Lead(Base):
    __tablename__="crm_leads"
    id=key(); user_code=word(); name=word(); email=word(); phone=word(); city=word(); state=word()
    proxy_name=word(); proxy_ip=word(); protocol=word(); status=word("Offline"); total_connections=number(0)
    data_used_mb=word("0.0"); interest=word(); stage=word("New"); trial=Column(Boolean,default=False)
    booking_id=fk("court_bookings",True); created=stamp()

class Shift(Base):
    __tablename__="bar_shifts"
    id=key(); staff_id=fk("users"); opened=stamp(); closed=Column(DateTime); summary=Column(JSON,default=dict)

class Leave(Base):
    __tablename__="hr_leaves"
    id=key(); staff_id=fk("users"); start=Column(Date); end=Column(Date); reason=word(); status=word("Pending")

class Payroll(Base):
    __tablename__="hr_payroll"
    id=key(); staff_id=fk("users"); period=word(); amount=number(); status=word("Recorded")

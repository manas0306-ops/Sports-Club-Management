"""
Pydantic Request & Response Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date

# ----------------- Member Schemas -----------------
class MemberCreateSchema(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    tier: str = "silver" # gold, silver, junior, walkin
    date_of_birth: Optional[date] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    duration_months: int = 12
    notes: Optional[str] = None

class MemberRenewSchema(BaseModel):
    member_id: int
    duration_months: int = 12

# ----------------- Court Schemas -----------------
class BookingCreateSchema(BaseModel):
    court_id: int
    start_time: datetime
    member_id: Optional[int] = None
    guest_name: Optional[str] = None
    guest_phone: Optional[str] = None
    guest_email: Optional[str] = None
    is_social_play: bool = False
    payment_method: str = "counter"

# ----------------- Shop Schemas -----------------
class CartItemSchema(BaseModel):
    product_id: int
    quantity: int = 1

class ShopSaleSchema(BaseModel):
    items: List[CartItemSchema]
    channel: str = "counter_pos" # counter_pos, online_click_collect, online_delivery
    member_id: Optional[int] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    delivery_address: Optional[str] = None
    payment_method: str = "cash"

class ProductRestockSchema(BaseModel):
    product_id: int
    quantity: int

# ----------------- Bar & KOT Schemas -----------------
class OpenTabSchema(BaseModel):
    table_id: Optional[int] = None
    member_id: Optional[int] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    server_staff_name: str = "Bar Staff"

class OrderItemInputSchema(BaseModel):
    menu_item_id: int
    quantity: int = 1
    notes: Optional[str] = None

class AddTabItemsSchema(BaseModel):
    tab_id: int
    items: List[OrderItemInputSchema]

class SettleTabSchema(BaseModel):
    tab_id: int
    payment_method: str = "card" # cash, card, upi
    tip_amount: float = 0.0

class UpdateKOTStatusSchema(BaseModel):
    order_item_id: int
    new_status: str # pending, preparing, ready, served

class DailyClosingSchema(BaseModel):
    staff_name: str = "Head Bartender"

# ----------------- CRM & Leads Schemas -----------------
class LeadCreateSchema(BaseModel):
    name: str
    email: str
    phone: str
    interested_sport: str = "tennis"
    interested_tier: str = "gold"
    source: str = "website_form"
    notes: Optional[str] = None

class TrialBookingSchema(BaseModel):
    visitor_name: str
    visitor_email: str
    visitor_phone: str
    sport_type: str = "tennis"
    trial_date: date
    trial_time_slot: str
    lead_id: Optional[int] = None

class QuoteCreateSchema(BaseModel):
    lead_id: int
    tier_proposed: str
    coaching_addon_fee: float = 0.0
    discount_amount: float = 0.0

class ConvertLeadSchema(BaseModel):
    lead_id: int
    tier: str = "silver"
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

# ----------------- Finance & HR Schemas -----------------
class InvoiceCreateSchema(BaseModel):
    client_name: str
    client_email: str
    invoice_type: str = "corporate_client"
    subtotal: float
    due_days: int = 15
    client_tax_id: Optional[str] = None
    client_address: Optional[str] = None
    notes: Optional[str] = None
    line_items_summary: Optional[str] = None
    member_id: Optional[int] = None

class InvoicePaymentSchema(BaseModel):
    invoice_id: int
    amount: float
    payment_method: str = "online"

class LeaveActionSchema(BaseModel):
    leave_id: int
    action: str # approve, reject
    reviewed_by: str = "Club Owner"
    review_notes: Optional[str] = None

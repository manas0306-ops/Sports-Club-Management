"""
Owner Financials, Consolidated Multi-Channel Reporting, Invoicing & HR Service
"""
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from fastapi import HTTPException

from app.models.court import CourtBooking
from app.models.shop import ShopOrder
from app.models.bar import BarTab
from app.models.finance import Invoice, Employee, StaffShift, LeaveRequest
from app.models.member import Member
from app.config import settings

def get_start_date_for_period(period: str) -> datetime:
    today = date.today()
    if period == "today":
        start_d = today
    elif period == "week":
        start_d = today - timedelta(days=today.weekday()) # Monday of current week
    elif period == "month":
        start_d = date(today.year, today.month, 1)
    else: # all
        start_d = date(2020, 1, 1)
    return datetime.combine(start_d, datetime.min.time())

def get_unified_financial_metrics(db: Session, period: str = "month") -> Dict[str, Any]:
    start_dt = get_start_date_for_period(period)
    
    # 1. Court Bookings Revenue
    court_bookings = db.query(CourtBooking).filter(
        CourtBooking.booking_date >= start_dt.date(),
        CourtBooking.booking_status != "cancelled",
        CourtBooking.payment_status == "paid"
    ).all()
    court_revenue = sum(b.total_amount for b in court_bookings)
    court_tax = sum(b.tax_amount for b in court_bookings)

    # 2. Gear Shop Revenue
    shop_orders = db.query(ShopOrder).filter(
        ShopOrder.created_at >= start_dt,
        ShopOrder.payment_status == "paid"
    ).all()
    shop_revenue = sum(o.total_amount for o in shop_orders)
    shop_tax = sum(o.tax_amount for o in shop_orders)

    # 3. Bar & Cafeteria Revenue
    bar_tabs = db.query(BarTab).filter(
        BarTab.status == "settled",
        BarTab.closed_at >= start_dt
    ).all()
    bar_revenue = sum(t.total_amount for t in bar_tabs)
    bar_tax = sum(t.tax_amount for t in bar_tabs)

    # 4. Membership Dues Invoices
    membership_invoices = db.query(Invoice).filter(
        Invoice.issue_date >= start_dt.date(),
        Invoice.invoice_type == "member_dues",
        Invoice.status == "paid"
    ).all()
    membership_revenue = sum(i.total_amount for i in membership_invoices)
    membership_tax = sum(i.tax_amount for i in membership_invoices)

    # 5. Corporate / Business Client Invoices
    corporate_invoices = db.query(Invoice).filter(
        Invoice.issue_date >= start_dt.date(),
        Invoice.invoice_type != "member_dues",
        Invoice.status == "paid"
    ).all()
    corporate_revenue = sum(i.total_amount for i in corporate_invoices)
    corporate_tax = sum(i.tax_amount for i in corporate_invoices)

    # 6. Receivables (What do we owe / What are we owed?)
    unpaid_invoices = db.query(Invoice).filter(
        Invoice.status.in_(["sent", "overdue"])
    ).all()
    total_receivables = sum(i.total_amount - i.amount_paid for i in unpaid_invoices)

    total_gross_revenue = court_revenue + shop_revenue + bar_revenue + membership_revenue + corporate_revenue
    total_tax_collected = court_tax + shop_tax + bar_tax + membership_tax + corporate_tax
    net_revenue = total_gross_revenue - total_tax_collected

    # 7. Payment Methods Aggregation (Cash, Card, UPI, Online)
    payment_methods = {"cash": 0.0, "card": 0.0, "upi": 0.0, "online": 0.0}
    
    for b in court_bookings:
        method = b.payment_method.lower() if b.payment_method else "cash"
        if method in payment_methods:
            payment_methods[method] += b.total_amount
        else:
            payment_methods["card"] += b.total_amount

    for o in shop_orders:
        method = o.payment_method.lower() if o.payment_method else "card"
        if method in payment_methods:
            payment_methods[method] += o.total_amount
        else:
            payment_methods["card"] += o.total_amount

    for t in bar_tabs:
        method = t.payment_method.lower() if t.payment_method else "upi"
        if method in payment_methods:
            payment_methods[method] += t.total_amount
        else:
            payment_methods["upi"] += t.total_amount

    for inv in membership_invoices + corporate_invoices:
        payment_methods["online"] += inv.total_amount

    # 8. Staff Payroll & Operating Expenses
    employees = db.query(Employee).filter(Employee.is_active == True).all()
    total_monthly_payroll = sum(e.monthly_salary for e in employees)

    return {
        "period": period,
        "total_revenue": round(total_gross_revenue, 2),
        "net_revenue": round(net_revenue, 2),
        "total_tax_collected": round(total_tax_collected, 2),
        "total_receivables": round(total_receivables, 2),
        "monthly_payroll_liability": round(total_monthly_payroll, 2),
        "estimated_profit": round(net_revenue - total_monthly_payroll, 2),
        "breakdown_by_source": {
            "courts": round(court_revenue, 2),
            "shop": round(shop_revenue, 2),
            "bar": round(bar_revenue, 2),
            "memberships": round(membership_revenue, 2),
            "corporate": round(corporate_revenue, 2)
        },
        "breakdown_by_payment_method": {
            "cash": round(payment_methods["cash"], 2),
            "card": round(payment_methods["card"], 2),
            "upi": round(payment_methods["upi"], 2),
            "online": round(payment_methods["online"], 2)
        },
        "counts": {
            "court_bookings": len(court_bookings),
            "shop_orders": len(shop_orders),
            "bar_tabs_settled": len(bar_tabs),
            "paid_invoices": len(membership_invoices) + len(corporate_invoices),
            "pending_invoices": len(unpaid_invoices)
        }
    }

def create_corporate_invoice(
    db: Session,
    client_name: str,
    client_email: str,
    invoice_type: str, # "corporate_client", "tournament_booking", "member_dues"
    subtotal: float,
    due_days: int = 15,
    client_tax_id: Optional[str] = None,
    client_address: Optional[str] = None,
    notes: Optional[str] = None,
    line_items_summary: Optional[str] = None,
    member_id: Optional[int] = None
) -> Invoice:
    tax_amount = round(subtotal * 0.18, 2)
    total_amount = round(subtotal + tax_amount, 2)
    
    count = db.query(Invoice).count() + 1
    inv_number = f"INV-{datetime.now().strftime('%Y%m')}-{count:04d}"

    invoice = Invoice(
        invoice_number=inv_number,
        invoice_type=invoice_type,
        member_id=member_id,
        client_name=client_name,
        client_email=client_email,
        client_tax_id=client_tax_id,
        client_address=client_address,
        issue_date=date.today(),
        due_date=date.today() + timedelta(days=due_days),
        subtotal=subtotal,
        tax_amount=tax_amount,
        total_amount=total_amount,
        amount_paid=0.0,
        status="sent",
        notes=notes,
        line_items_summary=line_items_summary
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice

def record_invoice_payment(
    db: Session,
    invoice_id: int,
    amount: float,
    payment_method: str = "online"
) -> Invoice:
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    inv.amount_paid += amount
    inv.payment_method = payment_method
    if inv.amount_paid >= inv.total_amount:
        inv.status = "paid"
    db.commit()
    db.refresh(inv)
    return inv

def approve_reject_leave(
    db: Session,
    leave_id: int,
    action: str, # "approve" or "reject"
    reviewed_by: str = "Club Owner",
    review_notes: Optional[str] = None
) -> LeaveRequest:
    leave = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")

    if action == "approve":
        leave.status = "approved"
    elif action == "reject":
        leave.status = "rejected"
    else:
        raise HTTPException(status_code=400, detail="Action must be 'approve' or 'reject'")

    leave.reviewed_by = reviewed_by
    leave.review_notes = review_notes
    db.commit()
    db.refresh(leave)
    return leave

"""
Owner Financials, Consolidated Multi-Channel Metrics, Invoicing & HR Router
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.finance import Invoice, Employee, StaffShift, LeaveRequest
from app.schemas.all_schemas import InvoiceCreateSchema, InvoicePaymentSchema, LeaveActionSchema
from app.services import finance_service

router = APIRouter(prefix="/finance", tags=["Owner Financials & HR"])

@router.get("/metrics")
def get_metrics(period: str = Query("month", pattern="^(today|week|month|all)$"), db: Session = Depends(get_db)):
    return finance_service.get_unified_financial_metrics(db, period=period)

@router.get("/invoices")
def list_invoices(status: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Invoice)
    if status:
        q = q.filter(Invoice.status == status)
    invoices = q.order_by(Invoice.issue_date.desc()).all()
    return [
        {
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "type": inv.invoice_type,
            "client_name": inv.client_name,
            "client_email": inv.client_email,
            "subtotal": inv.subtotal,
            "tax_amount": inv.tax_amount,
            "total_amount": inv.total_amount,
            "amount_paid": inv.amount_paid,
            "balance_due": round(inv.total_amount - inv.amount_paid, 2),
            "status": inv.status,
            "issue_date": str(inv.issue_date),
            "due_date": str(inv.due_date)
        }
        for inv in invoices
    ]

@router.post("/invoices")
def create_invoice(payload: InvoiceCreateSchema, db: Session = Depends(get_db)):
    inv = finance_service.create_corporate_invoice(
        db=db,
        client_name=payload.client_name,
        client_email=payload.client_email,
        invoice_type=payload.invoice_type,
        subtotal=payload.subtotal,
        due_days=payload.due_days,
        client_tax_id=payload.client_tax_id,
        client_address=payload.client_address,
        notes=payload.notes,
        line_items_summary=payload.line_items_summary,
        member_id=payload.member_id
    )
    return {
        "success": True,
        "message": f"Invoice {inv.invoice_number} created successfully.",
        "invoice_number": inv.invoice_number,
        "total_amount": inv.total_amount,
        "due_date": str(inv.due_date)
    }

@router.post("/invoices/pay")
def pay_invoice(payload: InvoicePaymentSchema, db: Session = Depends(get_db)):
    inv = finance_service.record_invoice_payment(
        db=db,
        invoice_id=payload.invoice_id,
        amount=payload.amount,
        payment_method=payload.payment_method
    )
    return {
        "success": True,
        "message": f"Payment of ₹{payload.amount} recorded for {inv.invoice_number}. Status: {inv.status.upper()}",
        "new_status": inv.status,
        "balance_remaining": round(inv.total_amount - inv.amount_paid, 2)
    }

@router.get("/hr/staff")
def list_employees(db: Session = Depends(get_db)):
    employees = db.query(Employee).all()
    return [
        {
            "id": e.id,
            "code": e.employee_code,
            "name": e.name,
            "role": e.role,
            "email": e.email,
            "phone": e.phone,
            "monthly_salary": e.monthly_salary,
            "is_active": e.is_active
        }
        for e in employees
    ]

@router.get("/hr/leaves")
def list_leaves(db: Session = Depends(get_db)):
    leaves = db.query(LeaveRequest).order_by(LeaveRequest.created_at.desc()).all()
    return [
        {
            "id": l.id,
            "employee_name": l.employee.name if l.employee else "Unknown",
            "role": l.employee.role if l.employee else "Staff",
            "leave_type": l.leave_type,
            "start_date": str(l.start_date),
            "end_date": str(l.end_date),
            "total_days": l.total_days,
            "reason": l.reason,
            "status": l.status,
            "reviewed_by": l.reviewed_by
        }
        for l in leaves
    ]

@router.post("/hr/leaves/action")
def leave_action(payload: LeaveActionSchema, db: Session = Depends(get_db)):
    leave = finance_service.approve_reject_leave(
        db=db,
        leave_id=payload.leave_id,
        action=payload.action,
        reviewed_by=payload.reviewed_by,
        review_notes=payload.review_notes
    )
    return {
        "success": True,
        "message": f"Leave request for {leave.employee.name} has been {leave.status.upper()}.",
        "status": leave.status
    }

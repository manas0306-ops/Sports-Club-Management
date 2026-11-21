"""
Bar, Cafeteria, KOT & Table Tracking API Router
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.bar import BarMenuItem
from app.schemas.all_schemas import (
    OpenTabSchema, AddTabItemsSchema, SettleTabSchema, UpdateKOTStatusSchema, DailyClosingSchema
)
from app.services import bar_service

router = APIRouter(prefix="/bar", tags=["Bar & Cafeteria"])

@router.get("/tables")
def list_tables(db: Session = Depends(get_db)):
    return bar_service.get_tables_overview(db)

@router.get("/menu")
def get_menu(db: Session = Depends(get_db)):
    items = db.query(BarMenuItem).filter(BarMenuItem.is_available == True).all()
    return [
        {
            "id": i.id,
            "name": i.name,
            "category": i.category,
            "price": i.price,
            "is_kitchen_item": i.is_kitchen_item,
            "description": i.description
        }
        for i in items
    ]

@router.post("/tabs/open")
def open_tab(payload: OpenTabSchema, db: Session = Depends(get_db)):
    tab = bar_service.open_tab(
        db=db,
        table_id=payload.table_id,
        member_id=payload.member_id,
        customer_name=payload.customer_name,
        customer_phone=payload.customer_phone,
        server_staff_name=payload.server_staff_name
    )
    return {
        "success": True,
        "message": f"Bar tab {tab.tab_number} opened successfully.",
        "tab_id": tab.id,
        "tab_number": tab.tab_number,
        "discount_percent": tab.discount_percent
    }

@router.post("/tabs/add-items")
def add_items_to_tab(payload: AddTabItemsSchema, db: Session = Depends(get_db)):
    tab = bar_service.add_items_to_tab(
        db=db,
        tab_id=payload.tab_id,
        items=[it.dict() for it in payload.items]
    )
    return {
        "success": True,
        "message": f"Added items to tab {tab.tab_number}. KOT sent to kitchen.",
        "tab_number": tab.tab_number,
        "subtotal": tab.subtotal,
        "discount_amount": tab.discount_amount,
        "tax_amount": tab.tax_amount,
        "total_amount": tab.total_amount
    }

@router.post("/tabs/settle")
def settle_tab(payload: SettleTabSchema, db: Session = Depends(get_db)):
    tab = bar_service.settle_tab(
        db=db,
        tab_id=payload.tab_id,
        payment_method=payload.payment_method,
        tip_amount=payload.tip_amount
    )
    return {
        "success": True,
        "message": f"Tab {tab.tab_number} settled in full via {tab.payment_method.upper()}.",
        "total_paid": tab.total_amount,
        "payment_method": tab.payment_method
    }

@router.get("/kitchen/tickets")
def get_kitchen_tickets(db: Session = Depends(get_db)):
    return bar_service.get_kitchen_display_orders(db)

@router.post("/kitchen/status")
def update_kot_status(payload: UpdateKOTStatusSchema, db: Session = Depends(get_db)):
    item = bar_service.update_kot_item_status(
        db=db,
        order_item_id=payload.order_item_id,
        new_status=payload.new_status
    )
    return {
        "success": True,
        "message": f"Ticket item '{item.item_name}' updated to {item.kot_status}."
    }

@router.post("/closing")
def perform_daily_closing(payload: DailyClosingSchema, db: Session = Depends(get_db)):
    closing = bar_service.generate_daily_closing_report(db, staff_name=payload.staff_name)
    return {
        "success": True,
        "closing_id": closing.id,
        "total_sales": closing.total_sales,
        "total_cash": closing.total_cash,
        "total_card": closing.total_card,
        "total_upi": closing.total_upi,
        "tax_total": closing.tax_total,
        "tabs_settled_count": closing.tabs_settled_count,
        "open_tabs_count": closing.open_tabs_count
    }

"""
Bar & Cafeteria POS, Running Tabs, KOT & End-of-Day Closing Service
"""
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from fastapi import HTTPException

from app.models.bar import BarTable, BarMenuItem, BarTab, BarOrderItem, BarDailyClosing
from app.models.member import Member
from app.config import settings

def generate_tab_number(db: Session) -> str:
    today_str = datetime.now().strftime("%Y%m%d")
    count = db.query(BarTab).count() + 1
    return f"TAB-{today_str}-{count:04d}"

def generate_kot_number(db: Session) -> str:
    count = db.query(BarOrderItem).count() + 1
    return f"KOT-{count:05d}"

def get_tables_overview(db: Session) -> List[Dict[str, Any]]:
    tables = db.query(BarTable).all()
    results = []
    for t in tables:
        active_tab = db.query(BarTab).filter(BarTab.table_id == t.id, BarTab.status == "open").first()
        results.append({
            "id": t.id,
            "table_number": t.table_number,
            "area": t.area,
            "capacity": t.capacity,
            "status": "occupied" if active_tab else t.status,
            "active_tab": {
                "id": active_tab.id,
                "tab_number": active_tab.tab_number,
                "customer_name": active_tab.customer_name,
                "total_amount": active_tab.total_amount,
                "items_count": len(active_tab.items)
            } if active_tab else None
        })
    return results

def open_tab(
    db: Session,
    table_id: Optional[int] = None,
    member_id: Optional[int] = None,
    customer_name: Optional[str] = None,
    customer_phone: Optional[str] = None,
    server_staff_name: str = "Bar Staff"
) -> BarTab:
    # If table is given, check if already occupied
    if table_id:
        existing_open = db.query(BarTab).filter(BarTab.table_id == table_id, BarTab.status == "open").first()
        if existing_open:
            raise HTTPException(status_code=400, detail=f"Table already has an open tab ({existing_open.tab_number}). Add items to that tab or settle it first.")

    member = None
    discount_pct = 0.0
    if member_id:
        member = db.query(Member).filter(Member.id == member_id).first()
        if member:
            tier_info = settings.TIERS.get(member.tier, settings.TIERS["walkin"])
            discount_pct = tier_info.get("bar_discount", 0.0)
            if not customer_name:
                customer_name = member.full_name
            if not customer_phone:
                customer_phone = member.phone

    if not customer_name:
        customer_name = "Walk-in Guest"

    tab = BarTab(
        tab_number=generate_tab_number(db),
        table_id=table_id,
        member_id=member_id,
        customer_name=customer_name,
        customer_phone=customer_phone,
        status="open",
        opened_at=datetime.utcnow(),
        discount_percent=round(discount_pct * 100, 1),
        server_staff_name=server_staff_name
    )
    
    if table_id:
        table = db.query(BarTable).filter(BarTable.id == table_id).first()
        if table:
            table.status = "occupied"

    db.add(tab)
    db.commit()
    db.refresh(tab)
    return tab

def add_items_to_tab(
    db: Session,
    tab_id: int,
    items: List[Dict[str, Any]] # [{"menu_item_id": int, "quantity": int, "notes": str}]
) -> BarTab:
    tab = db.query(BarTab).filter(BarTab.id == tab_id, BarTab.status == "open").first()
    if not tab:
        raise HTTPException(status_code=404, detail="Open tab not found")

    kot_ticket = generate_kot_number(db)
    
    for it in items:
        menu_item_id = it.get("menu_item_id")
        qty = it.get("quantity", 1)
        notes = it.get("notes", "")

        menu_item = db.query(BarMenuItem).filter(BarMenuItem.id == menu_item_id).first()
        if not menu_item or not menu_item.is_available:
            continue

        item_total = menu_item.price * qty
        order_item = BarOrderItem(
            tab_id=tab.id,
            menu_item_id=menu_item.id,
            item_name=menu_item.name,
            quantity=qty,
            unit_price=menu_item.price,
            total_price=item_total,
            kot_ticket_number=kot_ticket,
            kitchen_notes=notes,
            kot_status="pending" if menu_item.is_kitchen_item else "served",
            ordered_at=datetime.utcnow()
        )
        db.add(order_item)

    db.flush()

    # Recalculate Tab Totals with Member Auto-Discount
    all_items = db.query(BarOrderItem).filter(BarOrderItem.tab_id == tab.id).all()
    gross_subtotal = sum(i.total_price for i in all_items)
    
    # Auto Member Discount applied without asking!
    discount_pct = tab.discount_percent / 100.0
    discount_amount = round(gross_subtotal * discount_pct, 2)
    net_subtotal = round(gross_subtotal - discount_amount, 2)
    
    # 5% F&B GST
    tax_amount = round(net_subtotal * settings.TAX_RATE_BAR, 2)
    total_amount = round(net_subtotal + tax_amount, 2)

    tab.subtotal = gross_subtotal
    tab.discount_amount = discount_amount
    tab.tax_amount = tax_amount
    tab.total_amount = total_amount

    db.commit()
    db.refresh(tab)
    return tab

def settle_tab(
    db: Session,
    tab_id: int,
    payment_method: str = "card", # "cash", "card", "upi"
    tip_amount: float = 0.0
) -> BarTab:
    tab = db.query(BarTab).filter(BarTab.id == tab_id, BarTab.status == "open").first()
    if not tab:
        raise HTTPException(status_code=404, detail="Open tab not found")

    if payment_method not in ("cash", "card", "upi"):
        raise HTTPException(status_code=400, detail="Payment method must be cash, card, or upi")

    tab.status = "settled"
    tab.payment_method = payment_method
    tab.tip_amount = round(tip_amount, 2)
    tab.total_amount = round(tab.total_amount + tab.tip_amount, 2)
    tab.closed_at = datetime.utcnow()

    # Free the table
    if tab.table_id:
        table = db.query(BarTable).filter(BarTable.id == tab.table_id).first()
        if table:
            table.status = "available"

    db.commit()
    db.refresh(tab)
    return tab

def get_kitchen_display_orders(db: Session) -> List[Dict[str, Any]]:
    orders = db.query(BarOrderItem).filter(
        BarOrderItem.kot_status.in_(["pending", "preparing", "ready"])
    ).order_by(BarOrderItem.ordered_at).all()

    grouped_tickets = {}
    for ord_item in orders:
        t_num = ord_item.kot_ticket_number
        if t_num not in grouped_tickets:
            tab = ord_item.tab
            grouped_tickets[t_num] = {
                "kot_ticket_number": t_num,
                "tab_number": tab.tab_number if tab else "N/A",
                "table": tab.table.table_number if (tab and tab.table) else "Counter/Takeaway",
                "customer_name": tab.customer_name if tab else "Guest",
                "ordered_at": ord_item.ordered_at.strftime("%H:%M:%S"),
                "items": []
            }
        grouped_tickets[t_num]["items"].append({
            "order_item_id": ord_item.id,
            "item_name": ord_item.item_name,
            "quantity": ord_item.quantity,
            "kitchen_notes": ord_item.kitchen_notes,
            "kot_status": ord_item.kot_status
        })

    return list(grouped_tickets.values())

def update_kot_item_status(db: Session, order_item_id: int, new_status: str) -> BarOrderItem:
    if new_status not in ("pending", "preparing", "ready", "served"):
        raise HTTPException(status_code=400, detail="Invalid status")
    item = db.query(BarOrderItem).filter(BarOrderItem.id == order_item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Order item not found")
    item.kot_status = new_status
    db.commit()
    db.refresh(item)
    return item

def generate_daily_closing_report(db: Session, staff_name: str = "Manager") -> BarDailyClosing:
    today_start = datetime.combine(date.today(), datetime.min.time())
    
    settled_tabs = db.query(BarTab).filter(
        BarTab.status == "settled",
        BarTab.closed_at >= today_start
    ).all()
    
    total_sales = sum(t.total_amount for t in settled_tabs)
    total_cash = sum(t.total_amount for t in settled_tabs if t.payment_method == "cash")
    total_card = sum(t.total_amount for t in settled_tabs if t.payment_method == "card")
    total_upi = sum(t.total_amount for t in settled_tabs if t.payment_method == "upi")
    tax_total = sum(t.tax_amount for t in settled_tabs)
    
    open_tabs_count = db.query(BarTab).filter(BarTab.status == "open").count()

    closing = BarDailyClosing(
        closing_date=datetime.utcnow(),
        closed_by_staff=staff_name,
        total_sales=round(total_sales, 2),
        total_cash=round(total_cash, 2),
        total_card=round(total_card, 2),
        total_upi=round(total_upi, 2),
        tax_total=round(tax_total, 2),
        tabs_settled_count=len(settled_tabs),
        open_tabs_count=open_tabs_count
    )

    db.add(closing)
    db.commit()
    db.refresh(closing)
    return closing

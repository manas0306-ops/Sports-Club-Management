"""
Unified Pro Shop & Real-Time Inventory Service
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException

from app.models.shop import Product, ProductCategory, ShopOrder, ShopOrderItem
from app.models.member import Member
from app.config import settings

def generate_order_number(db: Session, channel: str) -> str:
    today_str = datetime.now().strftime("%Y%m%d")
    count = db.query(ShopOrder).count() + 1
    prefix = "POS" if channel == "counter_pos" else "WEB"
    return f"{prefix}-{today_str}-{count:04d}"

def get_product_catalog(db: Session, category_slug: Optional[str] = None, low_stock_only: bool = False) -> List[Dict[str, Any]]:
    query = db.query(Product).filter(Product.is_active == True)
    if category_slug:
        query = query.join(ProductCategory).filter(ProductCategory.slug == category_slug)
    
    products = query.order_by(Product.name).all()
    results = []
    for p in products:
        if low_stock_only and not p.is_low_stock:
            continue
        results.append({
            "id": p.id,
            "sku": p.sku,
            "name": p.name,
            "brand": p.brand,
            "category": p.category.name if p.category else "General",
            "category_slug": p.category.slug if p.category else "general",
            "retail_price": p.retail_price,
            "stock_quantity": p.stock_quantity,
            "reorder_level": p.reorder_level,
            "is_low_stock": p.is_low_stock,
            "image_url": p.image_url,
            "description": p.description
        })
    return results

def process_shop_sale(
    db: Session,
    items: List[Dict[str, Any]], # [{"product_id": int, "quantity": int}]
    channel: str = "counter_pos", # counter_pos, online_click_collect, online_delivery
    member_id: Optional[int] = None,
    customer_name: Optional[str] = None,
    customer_phone: Optional[str] = None,
    delivery_address: Optional[str] = None,
    payment_method: str = "cash"
) -> ShopOrder:
    if not items:
        raise HTTPException(status_code=400, detail="Cart cannot be empty")

    member = None
    discount_pct = 0.0
    if member_id:
        member = db.query(Member).filter(Member.id == member_id).first()
        if member:
            tier_info = settings.TIERS.get(member.tier, settings.TIERS["walkin"])
            discount_pct = tier_info.get("shop_discount", 0.0)
            if not customer_name:
                customer_name = member.full_name
            if not customer_phone:
                customer_phone = member.phone
    
    if not customer_name:
        customer_name = "Walk-in Guest"

    # UNIFIED INVENTORY: Verify shelf stock for every item before executing order
    order_items_to_create = []
    subtotal = 0.0

    for item in items:
        prod_id = item.get("product_id")
        qty = item.get("quantity", 1)
        if qty <= 0:
            continue

        product = db.query(Product).filter(Product.id == prod_id).with_for_update().first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product with ID {prod_id} not found")
        
        # Check stock on shared shelf
        if product.stock_quantity < qty:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for '{product.name}'. Requested: {qty}, Available on shelf: {product.stock_quantity}"
            )

        # Deduct stock immediately from the unified inventory
        product.stock_quantity -= qty

        line_gross = product.retail_price * qty
        line_discount = round(line_gross * discount_pct, 2)
        line_total = round(line_gross - line_discount, 2)
        subtotal += line_total

        order_items_to_create.append(
            ShopOrderItem(
                product_id=product.id,
                quantity=qty,
                unit_price=product.retail_price,
                discount_percent=round(discount_pct * 100, 1),
                total_price=line_total
            )
        )

    # 12% GST on gear
    total_discount = round(subtotal / (1.0 - discount_pct) * discount_pct, 2) if discount_pct > 0 else 0.0
    tax_amount = round(subtotal * settings.TAX_RATE_SHOP, 2)
    total_amount = round(subtotal + tax_amount, 2)

    order_status = "completed"
    if channel == "online_click_collect":
        order_status = "ready_for_pickup"
    elif channel == "online_delivery":
        order_status = "dispatched"

    order = ShopOrder(
        order_number=generate_order_number(db, channel),
        member_id=member.id if member else None,
        customer_name=customer_name,
        customer_phone=customer_phone,
        order_channel=channel,
        delivery_address=delivery_address,
        subtotal=round(subtotal, 2),
        discount_amount=total_discount,
        tax_amount=tax_amount,
        total_amount=total_amount,
        payment_method=payment_method,
        payment_status="paid",
        order_status=order_status,
        items=order_items_to_create
    )

    db.add(order)
    db.commit()
    db.refresh(order)
    return order

def restock_product(db: Session, product_id: int, quantity: int) -> Product:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.stock_quantity += quantity
    db.commit()
    db.refresh(product)
    return product

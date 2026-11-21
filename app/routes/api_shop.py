"""
Pro Shop & Unified Inventory API Router
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.schemas.all_schemas import ShopSaleSchema, ProductRestockSchema
from app.services import inventory_service

router = APIRouter(prefix="/shop", tags=["Pro Shop & Inventory"])

@router.get("/products")
def list_products(
    category: Optional[str] = Query(None),
    low_stock_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    return inventory_service.get_product_catalog(db, category_slug=category, low_stock_only=low_stock_only)

@router.post("/sale")
def process_sale(payload: ShopSaleSchema, db: Session = Depends(get_db)):
    order = inventory_service.process_shop_sale(
        db=db,
        items=[it.dict() for it in payload.items],
        channel=payload.channel,
        member_id=payload.member_id,
        customer_name=payload.customer_name,
        customer_phone=payload.customer_phone,
        delivery_address=payload.delivery_address,
        payment_method=payload.payment_method
    )
    return {
        "success": True,
        "message": f"Order {order.order_number} processed successfully ({order.order_channel}).",
        "order_number": order.order_number,
        "subtotal": order.subtotal,
        "discount_amount": order.discount_amount,
        "tax_amount": order.tax_amount,
        "total_amount": order.total_amount,
        "order_status": order.order_status,
        "items_count": len(order.items)
    }

@router.post("/restock")
def restock_item(payload: ProductRestockSchema, db: Session = Depends(get_db)):
    product = inventory_service.restock_product(db, product_id=payload.product_id, quantity=payload.quantity)
    return {
        "success": True,
        "message": f"Restocked {product.name}. New shelf stock: {product.stock_quantity}",
        "current_stock": product.stock_quantity
    }

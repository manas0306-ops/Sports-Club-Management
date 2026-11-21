"""
Unified Gear Shop & Inventory Models
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base

class ProductCategory(Base):
    __tablename__ = "product_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False) # Rackets, Balls, Shoes, Accessories, Apparel
    slug = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)

    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, index=True, nullable=False) # e.g. PRO-RK-001
    name = Column(String(150), nullable=False)
    category_id = Column(Integer, ForeignKey("product_categories.id"), nullable=False)
    brand = Column(String(100), default="Wilson")
    description = Column(Text, nullable=True)
    
    cost_price = Column(Float, default=0.0)
    retail_price = Column(Float, nullable=False)
    
    # Unified stock on the same shelf
    stock_quantity = Column(Integer, default=0, nullable=False)
    reorder_level = Column(Integer, default=5, nullable=False) # Low-stock threshold
    
    image_url = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    category = relationship("ProductCategory", back_populates="products")
    order_items = relationship("ShopOrderItem", back_populates="product")

    @property
    def is_low_stock(self) -> bool:
        return self.stock_quantity <= self.reorder_level

class ShopOrder(Base):
    __tablename__ = "shop_orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, index=True, nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=True)
    customer_name = Column(String(100), nullable=False)
    customer_phone = Column(String(30), nullable=True)
    
    # Counter POS vs Click & Collect vs Delivery
    order_channel = Column(String(50), default="counter_pos") # counter_pos, online_click_collect, online_delivery
    delivery_address = Column(Text, nullable=True)
    
    subtotal = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    
    payment_method = Column(String(30), default="cash") # cash, card, upi, online
    payment_status = Column(String(20), default="paid") # paid, pending, refunded
    order_status = Column(String(30), default="completed") # completed, ready_for_pickup, dispatched, cancelled
    
    created_at = Column(DateTime, default=datetime.utcnow)

    member = relationship("Member", back_populates="shop_orders")
    items = relationship("ShopOrderItem", back_populates="order", cascade="all, delete-orphan")

class ShopOrderItem(Base):
    __tablename__ = "shop_order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("shop_orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Float, nullable=False)
    discount_percent = Column(Float, default=0.0)
    total_price = Column(Float, nullable=False)

    order = relationship("ShopOrder", back_populates="items")
    product = relationship("Product", back_populates="order_items")

"""
The Champions Club - Application Configuration & Business Rules
"""
from pydantic_settings import BaseSettings
from typing import Dict, Any

class Settings(BaseSettings):
    PROJECT_NAME: str = "The Champions Club Management System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./champions_club.db"
    SECRET_KEY: str = "champions-club-odoo-super-secret-key-2026"
    
    # Membership Tier Configurations
    # Entitlements: court discount %, shop discount %, bar discount %, monthly fee
    TIERS: Dict[str, Dict[str, Any]] = {
        "gold": {
            "name": "Gold Tier",
            "code": "gold",
            "monthly_fee": 5000.0,
            "court_discount": 1.00,      # 100% free court access
            "shop_discount": 0.20,       # 20% discount on gear shop
            "bar_discount": 0.20,        # 20% discount at bar & cafeteria
            "description": "Premium full access to all club facilities with zero court fees and top discounts."
        },
        "silver": {
            "name": "Silver Tier",
            "code": "silver",
            "monthly_fee": 2500.0,
            "court_discount": 0.50,      # 50% discount on court fees
            "shop_discount": 0.10,       # 10% discount on gear shop
            "bar_discount": 0.10,        # 10% discount at bar & cafeteria
            "description": "Standard club membership with 50% court discount and member store privileges."
        },
        "junior": {
            "name": "Junior Tier",
            "code": "junior",
            "monthly_fee": 1500.0,
            "court_discount": 0.60,      # 60% discount on court fees (Under 18)
            "shop_discount": 0.10,       # 10% discount on gear shop
            "bar_discount": 0.05,        # 5% discount at bar & cafeteria
            "description": "Special rate for rising athletes under 18 years of age."
        },
        "walkin": {
            "name": "Walk-in / Guest",
            "code": "walkin",
            "monthly_fee": 0.0,
            "court_discount": 0.00,      # 0% discount (Full standard rate)
            "shop_discount": 0.00,
            "bar_discount": 0.00,
            "description": "Non-member walk-in rates."
        }
    }
    
    # Court Booking Rules
    SLOT_DURATION_MINUTES: int = 60          # Sessions last an hour
    SLOT_INTERVAL_MINUTES: int = 30          # New slot opens every 30 minutes
    MAX_DAILY_BOOKINGS_PER_MEMBER: int = 2   # Member can play at most twice a day
    CLUB_OPEN_HOUR: int = 6                  # 06:00 AM
    CLUB_CLOSE_HOUR: int = 22                # 10:00 PM
    
    # Standard Tax Rates
    TAX_RATE_COURTS: float = 0.18            # 18% GST/Service tax on sports facility
    TAX_RATE_SHOP: float = 0.12              # 12% GST on sports equipment
    TAX_RATE_BAR: float = 0.05               # 5% GST on F&B restaurant services

    class Config:
        case_sensitive = True

settings = Settings()

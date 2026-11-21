"""
Pytest configuration and test database fixtures
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from datetime import date, datetime, timedelta

from app.database import Base, get_db
from app.main import app
from app.models import (
    Member, Court, ProductCategory, Product, BarTable, BarMenuItem, Employee
)

from sqlalchemy.pool import StaticPool

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    # Seed basic fixtures for tests
    today = date.today()
    # Member fixtures
    m_gold = Member(
        member_code="TC-GOLD-TEST",
        first_name="Gold",
        last_name="Member",
        email="gold@test.com",
        phone="+91 99999 11111",
        tier="gold",
        status="active",
        expiry_date=today + timedelta(days=200)
    )
    m_silver = Member(
        member_code="TC-SILV-TEST",
        first_name="Silver",
        last_name="Member",
        email="silver@test.com",
        phone="+91 99999 22222",
        tier="silver",
        status="active",
        expiry_date=today + timedelta(days=100)
    )
    m_junior = Member(
        member_code="TC-JUNI-TEST",
        first_name="Junior",
        last_name="Member",
        email="junior@test.com",
        phone="+91 99999 33333",
        tier="junior",
        status="active",
        is_junior=True,
        expiry_date=today + timedelta(days=100)
    )
    session.add_all([m_gold, m_silver, m_junior])

    # Court fixtures
    court_tennis = Court(
        name="Test Tennis Court",
        sport_type="tennis",
        hourly_rate=800.0,
        is_active=True
    )
    court_cricket = Court(
        name="Test Cricket Net",
        sport_type="cricket",
        hourly_rate=1000.0,
        is_active=True
    )
    session.add_all([court_tennis, court_cricket])

    # Category and Product fixtures
    cat = ProductCategory(name="Gear", slug="gear")
    session.add(cat)
    session.flush()

    prod = Product(
        sku="TEST-BALLS",
        name="Test Tennis Balls",
        category_id=cat.id,
        retail_price=600.0,
        stock_quantity=10,
        reorder_level=3
    )
    session.add(prod)

    # Bar fixtures
    table = BarTable(table_number="T-TEST", capacity=4, status="available")
    menu_item = BarMenuItem(name="Protein Shake", category="shakes", price=200.0, is_kitchen_item=True)
    session.add_all([table, menu_item])

    session.commit()
    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

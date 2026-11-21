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
    User, UserRole, Guardian, PlayerProfile, AuditLog,
    Member, Court, ProductCategory, Product, BarTable, BarMenuItem, Employee
)
from app.services.auth_security import hash_password

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
    session.flush()

    # User Accounts fixtures (fast rounds=4 for blazing quick test execution)
    u_admin = User(
        username="admin_test",
        email="admin@test.com",
        password_hash=hash_password("AdminPass123!", rounds=4),
        primary_role="ADMIN",
        is_active=True,
        is_verified=True
    )
    u_member = User(
        username="member_test",
        email="gold@test.com",
        password_hash=hash_password("MemberPass123!", rounds=4),
        primary_role="MEMBER",
        is_active=True,
        is_verified=True
    )
    u_junior = User(
        username="junior_test",
        email="junior@test.com",
        password_hash=hash_password("MemberPass123!", rounds=4),
        primary_role="MEMBER",
        is_active=True,
        is_verified=True
    )
    u_player = User(
        username="player_test",
        email="player@test.com",
        password_hash=hash_password("PlayerPass123!", rounds=4),
        primary_role="PLAYER",
        is_active=True,
        is_verified=True
    )
    u_staff = User(
        username="staff_test",
        email="staff@test.com",
        password_hash=hash_password("StaffPass123!", rounds=4),
        primary_role="STAFF",
        is_active=True,
        is_verified=True
    )
    u_inactive = User(
        username="inactive_test",
        email="inactive@test.com",
        password_hash=hash_password("Secret123!", rounds=4),
        primary_role="MEMBER",
        is_active=False,
        is_verified=True
    )
    session.add_all([u_admin, u_member, u_junior, u_player, u_staff, u_inactive])
    session.flush()

    # Link member profiles
    m_gold.user_id = u_member.id
    m_junior.user_id = u_junior.id

    # Guardian fixture
    g_junior = Guardian(
        member_id=m_junior.id,
        guardian_name="Guardian Senior",
        relationship_type="Parent",
        contact_phone="+91 99999 44444",
        contact_email="guardian@test.com",
        consent_status="approved",
        consent_date=today
    )
    session.add(g_junior)

    # PlayerProfile fixture
    p_profile = PlayerProfile(
        user_id=u_player.id,
        athlete_name="Athlete Test",
        email="player@test.com",
        phone="+91 99999 55555",
        primary_sport="Tennis",
        skill_level="Professional",
        club_ranking="Seed #1",
        team_name="Champions Elite",
        training_schedule="Daily Drills",
        upcoming_matches="Match A vs B",
        match_history="Won 6-0 6-0",
        performance_metrics="First Serve: 80%"
    )
    session.add(p_profile)

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

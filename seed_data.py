"""
The Champions Club - Seed Data Generator
Preloads realistic club data covering all 6 scenes from the Odoo challenge problem.
"""
from datetime import date, datetime, timedelta, time
from app.database import SessionLocal, engine, Base
from app.models import (
    Member, Court, CourtBooking, ProductCategory, Product,
    BarTable, BarMenuItem, BarTab, BarOrderItem, BarDailyClosing,
    LeadEnquiry, TrialBooking, Quote, Invoice, Employee, StaffShift, LeaveRequest
)

def generate_members(today):
    first_names = [
        'Arjun', 'Kabir', 'Dev', 'Ishaan', 'Reyansh', 'Vivaan', 'Dhruv', 'Karan', 'Siddharth', 'Varun',
        'Manish', 'Nikhil', 'Gaurav', 'Akash', 'Tushar', 'Harsh', 'Pranav', 'Tanmay', 'Ayush', 'Samarth',
        'Yash', 'Rishi', 'Kartik', 'Ankit', 'Deepak', 'Suresh', 'Rahul', 'Mayank', 'Abhinav', 'Sachin',
        'Sunil', 'Vishal', 'Alok', 'Rajesh', 'Sameer', 'Farhan', 'Zayn', 'Arman', 'Neil', 'David',
        'Marcus', 'Liam', 'Alex', 'Lucas', 'Noah', 'Leo', 'Ethan', 'Kunal', 'Aditya', 'Madhav',
        'Sneha', 'Ananya', 'Rhea', 'Isha', 'Tara', 'Diya', 'Meera', 'Pooja', 'Kavya', 'Sanya',
        'Simran', 'Tanvi', 'Avani', 'Rupal', 'Kritika', 'Aditi', 'Shreya', 'Disha', 'Nisha', 'Neha',
        'Divya', 'Swati', 'Rashmi', 'Radhika', 'Bhavna', 'Pallavi', 'Smriti', 'Payal', 'Maya', 'Zara',
        'Elena', 'Sophia', 'Chloe', 'Emma', 'Olivia', 'Mia', 'Aria', 'Mila', 'Ella', 'Anushka'
    ]
    last_names = [
        'Patel', 'Kapoor', 'Iyer', 'Rao', 'Reddy', 'Banerjee', 'Chatterjee', 'Bose', 'Menon', 'Nair',
        'Pillai', 'Chopra', 'Singhania', 'Bhatia', 'Aggarwal', 'Jain', 'Gupta', 'Mittal', 'Trivedi', 'Pandey',
        'Mishra', 'Dubey', 'Tripathi', 'Choudhury', 'Das', 'Sengupta', 'Dutta', 'Mukherjee', 'Kulkarni', 'Deshmukh',
        'Patil', 'Joshi', 'Bhide', 'Apte', 'Sawant', 'Khan', 'Ahmed', 'Ansari', 'Qureshi', 'Mirza',
        'Smith', 'Taylor', 'Miller', 'Wilson', 'Anderson', 'Thomas', 'Sen', 'Vaidya', 'Bhatt', 'Nambiar'
    ]
    sports = ['Tennis', 'Cricket', 'Padel', 'Badminton', 'Fitness']

    # 4 foundational demonstration members from original challenge scenes
    members = [
        Member(
            member_code="TC-GOLD-0001",
            first_name="Rohan",
            last_name="Sharma",
            email="rohan.sharma@example.com",
            phone="+91 98200 11223",
            date_of_birth=date(1990, 5, 14),
            is_junior=False,
            tier="gold",
            status="active",
            start_date=today - timedelta(days=120),
            expiry_date=today + timedelta(days=245),
            emergency_contact_name="Ananya Sharma",
            emergency_contact_phone="+91 98200 99887",
            notes="Plays 3x weekly. Preferred court: Tennis Centre.",
            photo_url="https://api.dicebear.com/7.x/initials/svg?seed=Rohan+Sharma"
        ),
        Member(
            member_code="TC-SILV-0002",
            first_name="Priya",
            last_name="Verma",
            email="priya.verma@example.com",
            phone="+91 98111 22334",
            date_of_birth=date(1994, 8, 22),
            is_junior=False,
            tier="silver",
            status="active",
            start_date=today - timedelta(days=60),
            expiry_date=today + timedelta(days=120),
            emergency_contact_name="Sunil Verma",
            emergency_contact_phone="+91 98111 55667",
            notes="Attends weekend intermediate tennis clinics.",
            photo_url="https://api.dicebear.com/7.x/initials/svg?seed=Priya+Verma"
        ),
        Member(
            member_code="TC-JUNI-0003",
            first_name="Aarav",
            last_name="Mehta",
            email="aarav.junior@example.com",
            phone="+91 97654 32100",
            date_of_birth=date(2011, 3, 10),
            is_junior=True,
            tier="junior",
            status="active",
            start_date=today - timedelta(days=30),
            expiry_date=today + timedelta(days=335),
            emergency_contact_name="Karan Mehta (Father)",
            emergency_contact_phone="+91 97654 99999",
            notes="Junior State Championship squad trainee.",
            photo_url="https://api.dicebear.com/7.x/initials/svg?seed=Aarav+Mehta"
        ),
        Member(
            member_code="TC-GOLD-0004",
            first_name="Vikram",
            last_name="Malhotra",
            email="vikram.malhotra@example.com",
            phone="+91 99000 88776",
            date_of_birth=date(1982, 11, 4),
            is_junior=False,
            tier="gold",
            status="expired",
            start_date=today - timedelta(days=380),
            expiry_date=today - timedelta(days=15),
            emergency_contact_name="Meera Malhotra",
            emergency_contact_phone="+91 99000 11223",
            notes="Membership expired. Front desk flagged for renewal call.",
            photo_url="https://api.dicebear.com/7.x/initials/svg?seed=Vikram+Malhotra"
        )
    ]

    name_idx = 0
    def get_next_name():
        nonlocal name_idx
        fn = first_names[(name_idx * 7) % len(first_names)]
        ln = last_names[(name_idx * 11 + 3) % len(last_names)]
        name_idx += 1
        return fn, ln

    # 1. 33 more Gold members (making 35 Gold total)
    gold_codes = [f"TC-GOLD-{i:04d}" for i in range(5, 40) if i not in (1, 4)][:33]
    for idx, code in enumerate(gold_codes, start=5):
        fn, ln = get_next_name()
        is_expired = (idx % 8 == 0)
        status = "expired" if is_expired else "active"
        s_date = today - timedelta(days=390 if is_expired else (idx * 9 % 250 + 20))
        e_date = today - timedelta(days=(idx % 30 + 5)) if is_expired else today + timedelta(days=(idx * 11 % 300 + 40))
        members.append(Member(
            member_code=code,
            first_name=fn,
            last_name=ln,
            email=f"{fn.lower()}.{ln.lower()}.{idx}@champions.club",
            phone=f"+91 98{idx:03d} {idx*137%90000 + 10000:05d}",
            date_of_birth=date(1975 + (idx % 25), (idx % 12) + 1, (idx % 28) + 1),
            is_junior=False,
            tier="gold",
            status=status,
            start_date=s_date,
            expiry_date=e_date,
            emergency_contact_name=f"{ln} Family",
            emergency_contact_phone=f"+91 97{idx:03d} {idx*211%90000 + 10000:05d}",
            notes=f"Gold Tier Pass. Plays {sports[idx % len(sports)]} 3x weekly.",
            photo_url=f"https://api.dicebear.com/7.x/initials/svg?seed={fn}+{ln}"
        ))

    # 2. 64 more Silver members (making 65 Silver total)
    silv_codes = [f"TC-SILV-{i:04d}" for i in range(1, 75) if i != 2][:64]
    for idx, code in enumerate(silv_codes, start=101):
        fn, ln = get_next_name()
        is_expired = (idx % 7 == 0)
        is_pending = (idx % 19 == 0)
        status = "expired" if is_expired else ("pending" if is_pending else "active")
        s_date = today - timedelta(days=400 if is_expired else (idx * 5 % 200 + 10))
        e_date = today - timedelta(days=(idx % 40 + 2)) if is_expired else today + timedelta(days=(idx * 7 % 310 + 20))
        members.append(Member(
            member_code=code,
            first_name=fn,
            last_name=ln,
            email=f"{fn.lower()}.{ln.lower()}.{idx}@champions.club",
            phone=f"+91 96{idx:03d} {idx*149%90000 + 10000:05d}",
            date_of_birth=date(1980 + (idx % 24), (idx % 12) + 1, (idx % 28) + 1),
            is_junior=False,
            tier="silver",
            status=status,
            start_date=s_date,
            expiry_date=e_date,
            emergency_contact_name=f"{fn} Emergency Contact",
            emergency_contact_phone=f"+91 95{idx:03d} {idx*163%90000 + 10000:05d}",
            notes=f"Standard Silver Pass. Enjoys {sports[idx % len(sports)]}.",
            photo_url=f"https://api.dicebear.com/7.x/initials/svg?seed={fn}+{ln}"
        ))

    # 3. 34 more Junior members (making 35 Junior total)
    juni_codes = [f"TC-JUNI-{i:04d}" for i in range(1, 45) if i != 3][:34]
    for idx, code in enumerate(juni_codes, start=201):
        fn, ln = get_next_name()
        is_expired = (idx % 9 == 0)
        status = "expired" if is_expired else "active"
        s_date = today - timedelta(days=375 if is_expired else (idx * 4 % 180 + 15))
        e_date = today - timedelta(days=(idx % 25 + 1)) if is_expired else today + timedelta(days=(idx * 9 % 320 + 30))
        dob = date(2009 + (idx % 6), (idx % 12) + 1, (idx % 28) + 1)
        members.append(Member(
            member_code=code,
            first_name=fn,
            last_name=ln,
            email=f"{fn.lower()}.{ln.lower()}.{idx}@champions.club",
            phone=f"+91 94{idx:03d} {idx*179%90000 + 10000:05d}",
            date_of_birth=dob,
            is_junior=True,
            tier="junior",
            status=status,
            start_date=s_date,
            expiry_date=e_date,
            emergency_contact_name=f"{ln} (Parent Guardian)",
            emergency_contact_phone=f"+91 93{idx:03d} {idx*191%90000 + 10000:05d}",
            notes=f"Junior Athlete Academy squad ({sports[idx % len(sports)]}).",
            photo_url=f"https://api.dicebear.com/7.x/initials/svg?seed={fn}+{ln}"
        ))

    # 4. 30 Walk-in Guests (making 30 Walk-in total)
    walk_codes = [f"TC-WALK-{i:04d}" for i in range(1, 31)]
    for idx, code in enumerate(walk_codes, start=301):
        fn, ln = get_next_name()
        s_date = today - timedelta(days=(idx * 3 % 90 + 2))
        e_date = today + timedelta(days=365)
        members.append(Member(
            member_code=code,
            first_name=fn,
            last_name=ln,
            email=f"{fn.lower()}.{ln.lower()}.{idx}@guest.champions.club",
            phone=f"+91 92{idx:03d} {idx*223%90000 + 10000:05d}",
            date_of_birth=date(1982 + (idx % 22), (idx % 12) + 1, (idx % 28) + 1),
            is_junior=False,
            tier="walkin",
            status="active",
            start_date=s_date,
            expiry_date=e_date,
            emergency_contact_name=f"{fn} Family",
            emergency_contact_phone=f"+91 91{idx:03d} {idx*239%90000 + 10000:05d}",
            notes=f"Walk-in / Pay-per-play visitor for {sports[idx % len(sports)]}. Standard rate.",
            photo_url=f"https://api.dicebear.com/7.x/initials/svg?seed={fn}+{ln}"
        ))

    return members

def seed_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("Seeding The Champions Club database...")

    # 1. Seed Members (165 total: 35 Gold, 65 Silver, 35 Junior, 30 Walk-in)
    today = date.today()
    members = generate_members(today)
    db.add_all(members)
    db.commit()
    print(f"Successfully seeded {len(members)} realistic members (Gold, Silver, Junior, Walk-in).")

    # 2. Seed Courts (Scene 2: Tennis, Cricket, Padel)
    courts = [
        Court(
            name="Centre Tennis Court 1",
            sport_type="tennis",
            surface_type="clay",
            has_floodlights=True,
            hourly_rate=800.0,
            description="Championship red clay court with LED night floodlights."
        ),
        Court(
            name="Clay Tennis Court 2",
            sport_type="tennis",
            surface_type="clay",
            has_floodlights=True,
            hourly_rate=800.0,
            description="Outdoor clay court, ideal for baseline rallies."
        ),
        Court(
            name="Cricket Practice Net A",
            sport_type="cricket",
            surface_type="synthetic_turf",
            has_floodlights=True,
            hourly_rate=1000.0,
            description="Pace bowling cricket net with professional bowling machine."
        ),
        Court(
            name="Cricket Match Net B",
            sport_type="cricket",
            surface_type="turf",
            has_floodlights=True,
            hourly_rate=1000.0,
            description="Natural turf batting pitch with floodlights."
        ),
        Court(
            name="Panoramic Padel Court 1",
            sport_type="padel",
            surface_type="synthetic",
            has_floodlights=True,
            hourly_rate=900.0,
            description="State-of-the-art glass enclosed padel court."
        )
    ]
    db.add_all(courts)
    db.commit()

    # 3. Seed Existing Court Bookings for Today
    m1 = members[0] # Rohan (Gold)
    c1 = courts[0]  # Tennis 1
    c3 = courts[2]  # Cricket Net A

    b1_start = datetime.combine(today, time(18, 0)) # 6:00 PM busy evening
    b1_end = b1_start + timedelta(minutes=60)
    booking1 = CourtBooking(
        booking_reference="BK-" + today.strftime("%Y%m%d") + "-0001",
        court_id=c1.id,
        member_id=m1.id,
        guest_name=m1.full_name,
        guest_phone=m1.phone,
        guest_email=m1.email,
        booking_date=today,
        start_time=b1_start,
        end_time=b1_end,
        duration_minutes=60,
        is_social_play=False,
        base_rate=800.0,
        discount_percent=100.0, # Gold 100% Free
        discount_amount=800.0,
        final_court_fee=0.0,
        tax_amount=0.0,
        total_amount=0.0,
        payment_status="complimentary",
        booking_status="confirmed"
    )
    db.add(booking1)
    db.commit()

    # 4. Seed Product Categories & Unified Inventory Products (Scene 3)
    cat_rackets = ProductCategory(name="Rackets", slug="rackets", description="Tennis & Padel rackets")
    cat_balls = ProductCategory(name="Balls", slug="balls", description="Championship balls & cans")
    cat_shoes = ProductCategory(name="Footwear", slug="shoes", description="Court shoes")
    cat_accessories = ProductCategory(name="Accessories", slug="accessories", description="Grips, dampeners, bags")
    cat_apparel = ProductCategory(name="Apparel", slug="apparel", description="Dry-FIT sportswear")
    db.add_all([cat_rackets, cat_balls, cat_shoes, cat_accessories, cat_apparel])
    db.commit()

    products = [
        Product(
            sku="PRO-RK-001",
            name="Wilson Pro Staff 97 v14 Tennis Racket",
            category_id=cat_rackets.id,
            brand="Wilson",
            cost_price=13000.0,
            retail_price=18500.0,
            stock_quantity=3, # Low stock alert! (<=5)
            reorder_level=5,
            image_url="https://images.unsplash.com/photo-1617083934555-ac7d4fed89c9?w=300"
        ),
        Product(
            sku="PRO-RK-002",
            name="Babolat Pure Aero 2023 Racket",
            category_id=cat_rackets.id,
            brand="Babolat",
            cost_price=12000.0,
            retail_price=16999.0,
            stock_quantity=8,
            reorder_level=3,
            image_url="https://images.unsplash.com/photo-1617083934555-ac7d4fed89c9?w=300"
        ),
        Product(
            sku="PRO-BL-001",
            name="Wilson US Open Championship Tennis Balls (Can of 3)",
            category_id=cat_balls.id,
            brand="Wilson",
            cost_price=420.0,
            retail_price=650.0,
            stock_quantity=48,
            reorder_level=15,
            image_url="https://images.unsplash.com/photo-1599474924187-334a4ae5bd3c?w=300"
        ),
        Product(
            sku="PRO-SH-001",
            name="Asics Gel-Resolution 9 Clay Court Shoes",
            category_id=cat_shoes.id,
            brand="Asics",
            cost_price=8000.0,
            retail_price=11999.0,
            stock_quantity=2, # Low stock alert! (<=4)
            reorder_level=4,
            image_url="https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=300"
        ),
        Product(
            sku="PRO-AP-001",
            name="Nike Court Advantage Dry-FIT Polo",
            category_id=cat_apparel.id,
            brand="Nike",
            cost_price=1500.0,
            retail_price=2499.0,
            stock_quantity=18,
            reorder_level=5,
            image_url="https://images.unsplash.com/photo-1581655353564-df123a1eb820?w=300"
        ),
        Product(
            sku="PRO-AC-001",
            name="Yonex Super Grap Overgrip (Pack of 3)",
            category_id=cat_accessories.id,
            brand="Yonex",
            cost_price=220.0,
            retail_price=450.0,
            stock_quantity=35,
            reorder_level=10,
            image_url="https://images.unsplash.com/photo-1587280501635-68a0e82cd5ff?w=300"
        ),
        Product(
            sku="PRO-CR-001",
            name="SG Club Leather Cricket Match Ball",
            category_id=cat_balls.id,
            brand="SG",
            cost_price=550.0,
            retail_price=850.0,
            stock_quantity=24,
            reorder_level=8,
            image_url="https://images.unsplash.com/photo-1531415074868-036b10f05140?w=300"
        )
    ]
    db.add_all(products)
    db.commit()

    # 5. Seed Bar Tables & Menu Items (Scene 4)
    tables = [
        BarTable(table_number="T-01", area="main_hall", capacity=4, status="occupied"),
        BarTable(table_number="T-02", area="main_hall", capacity=4, status="available"),
        BarTable(table_number="T-03", area="main_hall", capacity=6, status="available"),
        BarTable(table_number="Patio-1", area="terrace", capacity=4, status="available"),
        BarTable(table_number="Patio-2", area="terrace", capacity=4, status="available"),
        BarTable(table_number="Lounge-A", area="lounge", capacity=8, status="available"),
        BarTable(table_number="Bar-01", area="bar_counter", capacity=2, status="available"),
        BarTable(table_number="Bar-02", area="bar_counter", capacity=2, status="available")
    ]
    db.add_all(tables)
    db.commit()

    menu_items = [
        BarMenuItem(name="Post-Match Whey Protein Shake (Chocolate)", category="shakes", price=250.0, is_kitchen_item=True, description="30g protein with banana & almond milk"),
        BarMenuItem(name="Electrolyte Hydration Drink (Lemon & Mint)", category="mocktails", price=120.0, is_kitchen_item=False, description="Chilled sports electrolytes"),
        BarMenuItem(name="Grilled Chicken Avocado Multigrain Panini", category="meals", price=320.0, is_kitchen_item=True, description="Served with roasted potato wedges"),
        BarMenuItem(name="Champions Gourmet Burger & French Fries", category="meals", price=380.0, is_kitchen_item=True, description="Juicy patty with sharp cheddar"),
        BarMenuItem(name="Cold Brewed Premium Lager Beer (Pint)", category="drinks_beers", price=350.0, is_kitchen_item=False, description="Crisp post-match refreshing beer"),
        BarMenuItem(name="Hummus & Grilled Pita Platter", category="snacks", price=240.0, is_kitchen_item=True, description="Fresh olive oil and crisp veggies")
    ]
    db.add_all(menu_items)
    db.commit()

    # Create an Open Tab with KOT tickets on Table T-01 for Member Rohan (Gold: 20% auto-discount)
    tab1 = BarTab(
        tab_number="TAB-" + today.strftime("%Y%m%d") + "-0001",
        table_id=tables[0].id,
        member_id=m1.id,
        customer_name=m1.full_name,
        customer_phone=m1.phone,
        status="open",
        opened_at=datetime.utcnow() - timedelta(minutes=45),
        discount_percent=20.0, # Gold 20% auto-applied!
        subtotal=890.0,
        discount_amount=178.0,
        tax_amount=35.6,
        total_amount=747.6,
        server_staff_name="Rajesh (Bar Lead)"
    )
    db.add(tab1)
    db.commit()

    order_items = [
        BarOrderItem(
            tab_id=tab1.id,
            menu_item_id=menu_items[2].id, # Chicken Panini
            item_name=menu_items[2].name,
            quantity=2,
            unit_price=320.0,
            total_price=640.0,
            kot_ticket_number="KOT-00001",
            kitchen_notes="Well toasted, extra crisp wedges",
            kot_status="preparing",
            ordered_at=datetime.utcnow() - timedelta(minutes=30)
        ),
        BarOrderItem(
            tab_id=tab1.id,
            menu_item_id=menu_items[0].id, # Protein Shake
            item_name=menu_items[0].name,
            quantity=1,
            unit_price=250.0,
            total_price=250.0,
            kot_ticket_number="KOT-00001",
            kitchen_notes="No added sugar",
            kot_status="ready",
            ordered_at=datetime.utcnow() - timedelta(minutes=30)
        )
    ]
    db.add_all(order_items)
    db.commit()

    # 6. Seed CRM Leads & Quotes (Scene 5)
    leads = [
        LeadEnquiry(
            enquiry_number="LEAD-202611-0001",
            name="Amit Kapoor",
            email="amit.kapoor@techcorp.in",
            phone="+91 99887 76655",
            interested_sport="tennis",
            interested_tier="gold",
            source="website_form",
            status="quote_sent",
            notes="Found club on Google. Looking for Gold membership with personal coaching.",
            follow_up_date=today + timedelta(days=2)
        ),
        LeadEnquiry(
            enquiry_number="LEAD-202611-0002",
            name="Sara Khan",
            email="sara.khan@designstudio.com",
            phone="+91 98765 11223",
            interested_sport="tennis",
            interested_tier="silver",
            source="website_form",
            status="trial_scheduled",
            notes="Booked trial session on Sunday with Coach David.",
            follow_up_date=today + timedelta(days=1)
        ),
        LeadEnquiry(
            enquiry_number="LEAD-202611-0003",
            name="Kunal Singhania",
            email="kunal.singhania@fintech.co",
            phone="+91 91234 98765",
            interested_sport="cricket",
            interested_tier="gold",
            source="phone_call",
            status="contacted",
            notes="Enquiring for weekend cricket net slot booking for office team.",
            follow_up_date=today + timedelta(days=3)
        )
    ]
    db.add_all(leads)
    db.commit()

    # Add Quote for Amit Kapoor
    q1 = Quote(
        quote_number="QT-202611-0001",
        lead_id=leads[0].id,
        customer_name=leads[0].name,
        customer_email=leads[0].email,
        plan_tier="gold",
        membership_fee=60000.0,
        coaching_addon_fee=12000.0,
        discount_amount=5000.0,
        tax_amount=12060.0,
        total_quote_amount=79060.0,
        valid_until=today + timedelta(days=14),
        terms="Annual Gold Membership package including 20 private coaching sessions.",
        status="sent"
    )
    db.add(q1)

    # Add Trial for Sara Khan
    t1 = TrialBooking(
        trial_reference="TRL-202611-0001",
        lead_id=leads[1].id,
        visitor_name=leads[1].name,
        visitor_email=leads[1].email,
        visitor_phone=leads[1].phone,
        sport_type="tennis",
        trial_date=today + timedelta(days=2),
        trial_time_slot="10:00 - 11:00",
        assigned_coach="Coach David (Head Pro)",
        status="scheduled"
    )
    db.add(t1)
    db.commit()

    # 7. Seed Owner Finance, Invoices & HR Staff (Scene 6)
    employees = [
        Employee(employee_code="EMP-001", name="David Miller", role="head_coach", email="david.pro@championsclub.in", phone="+91 99111 00001", monthly_salary=65000.0),
        Employee(employee_code="EMP-002", name="Anita Roy", role="front_desk", email="anita.frontdesk@championsclub.in", phone="+91 99111 00002", monthly_salary=32000.0),
        Employee(employee_code="EMP-003", name="Rajesh Kumar", role="bartender", email="rajesh.bar@championsclub.in", phone="+91 99111 00003", monthly_salary=28000.0),
        Employee(employee_code="EMP-004", name="Suresh Patil", role="court_maintenance", email="suresh.turf@championsclub.in", phone="+91 99111 00004", monthly_salary=24000.0)
    ]
    db.add_all(employees)
    db.commit()

    # Employee Shifts
    shifts = [
        StaffShift(employee_id=employees[0].id, shift_date=today, start_time="07:00", end_time="15:00", department="courts", status="scheduled"),
        StaffShift(employee_id=employees[1].id, shift_date=today, start_time="08:00", end_time="16:00", department="front_desk", status="clocked_in"),
        StaffShift(employee_id=employees[2].id, shift_date=today, start_time="14:00", end_time="22:00", department="bar_kitchen", status="clocked_in"),
        StaffShift(employee_id=employees[3].id, shift_date=today, start_time="06:00", end_time="14:00", department="maintenance", status="completed")
    ]
    db.add_all(shifts)

    # Leave Request
    leaves = [
        LeaveRequest(
            employee_id=employees[2].id, # Rajesh (Bartender)
            leave_type="casual",
            start_date=today + timedelta(days=5),
            end_date=today + timedelta(days=6),
            total_days=2,
            reason="Family function in hometown",
            status="pending"
        ),
        LeaveRequest(
            employee_id=employees[3].id, # Suresh
            leave_type="annual",
            start_date=today - timedelta(days=10),
            end_date=today - timedelta(days=8),
            total_days=3,
            reason="Annual planned leave",
            status="approved",
            reviewed_by="Club Owner"
        )
    ]
    db.add_all(leaves)

    # Invoices (Corporate & Member Dues)
    invoices = [
        Invoice(
            invoice_number="INV-202611-0001",
            invoice_type="corporate_client",
            client_name="Google India Sports Club",
            client_email="sports-committee@google.com",
            client_tax_id="29AAACG0561K1Z5",
            issue_date=today - timedelta(days=10),
            due_date=today + timedelta(days=5),
            subtotal=55000.0,
            tax_amount=9900.0,
            total_amount=64900.0,
            amount_paid=64900.0, # Fully paid
            status="paid",
            payment_method="online",
            line_items_summary="Quarterly Corporate Tennis & Cricket Court Reservation (40 court hours)"
        ),
        Invoice(
            invoice_number="INV-202611-0002",
            invoice_type="tournament_booking",
            client_name="Deloitte Bangalore Cricket League",
            client_email="events@deloitte.com",
            client_tax_id="29AACCD1234F1Z8",
            issue_date=today - timedelta(days=3),
            due_date=today + timedelta(days=12),
            subtotal=38000.0,
            tax_amount=6840.0,
            total_amount=44840.0,
            amount_paid=0.0, # Outstanding receivable
            status="sent",
            line_items_summary="Weekend Floodlit Cricket Tournament Net Rental + Referee Services"
        )
    ]
    db.add_all(invoices)
    db.commit()

    db.close()
    print("Database seeding completed successfully!")

if __name__ == "__main__":
    seed_database()

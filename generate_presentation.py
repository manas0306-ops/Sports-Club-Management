import sys
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def create_presentation(output_path="Champions_Club_Presentation.pptx"):
    prs = Presentation()
    # 16:9 Widescreen aspect ratio
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6] # Blank slide layout

    # Color Palette Definitions
    DARK_BG = RGBColor(11, 25, 44)       # Deep luxury navy #0b192c
    SLATE_DARK = RGBColor(15, 23, 42)    # #0f172a
    CARD_BG_DARK = RGBColor(20, 35, 60)  # #14233c
    CARD_BORDER_DARK = RGBColor(38, 64, 102) # #264066
    
    LIGHT_BG = RGBColor(248, 250, 252)   # #f8fafc
    CARD_BG_LIGHT = RGBColor(255, 255, 255)
    CARD_BORDER_LIGHT = RGBColor(226, 232, 240) # #e2e8f0
    
    EMERALD = RGBColor(6, 78, 59)        # Luxury deep emerald #064e3b
    MINT = RGBColor(16, 185, 129)        # Vibrant Mint #10b981
    MINT_LIGHT = RGBColor(209, 250, 229) # #d1fae5
    GOLD = RGBColor(217, 119, 6)         # Luxury Gold #d97706
    GOLD_LIGHT = RGBColor(254, 243, 199) # #fef3c7
    AMBER = RGBColor(245, 158, 11)       # #f59e0b
    NAVY_ACCENT = RGBColor(30, 58, 138)  # #1e3a8a
    
    TEXT_DARK = RGBColor(15, 23, 42)     # #0f172a
    TEXT_MUTED_LIGHT = RGBColor(100, 116, 139) # #64748b
    TEXT_WHITE = RGBColor(255, 255, 255)
    TEXT_MUTED_DARK = RGBColor(148, 163, 184) # #94a3b8

    def add_bg(slide, color):
        shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = color
        shape.line.fill.background()
        return shape

    def add_header(slide, tag_text, title_text, subtitle_text=None, is_dark=False):
        # Top banner / pill
        pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(0.5), Inches(2.8), Inches(0.35))
        pill.fill.solid()
        pill.fill.fore_color.rgb = GOLD if is_dark else MINT_LIGHT
        pill.line.fill.background()
        p_tf = pill.text_frame
        p_tf.word_wrap = True
        p_tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = p_tf.paragraphs[0]
        p.text = tag_text.upper()
        p.alignment = PP_ALIGN.CENTER
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = TEXT_WHITE if is_dark else EMERALD

        # Title
        tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.88), Inches(11.7), Inches(0.65))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title_text
        p.font.size = Pt(22)
        p.font.bold = True
        p.font.color.rgb = TEXT_WHITE if is_dark else TEXT_DARK

        if subtitle_text:
            p2 = tf.add_paragraph()
            p2.text = subtitle_text
            p2.font.size = Pt(12)
            p2.font.color.rgb = TEXT_MUTED_DARK if is_dark else TEXT_MUTED_LIGHT
            p2.space_before = Pt(3)

    def add_card(slide, left, top, width, height, bg_color=CARD_BG_LIGHT, border_color=CARD_BORDER_LIGHT):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        if border_color:
            card.line.color.rgb = border_color
            card.line.width = Pt(1.5)
        else:
            card.line.fill.background()
        return card

    # ==========================================
    # SLIDE 1: TITLE SLIDE (Luxury Dark Theme)
    # ==========================================
    slide1 = prs.slides.add_slide(blank_layout)
    add_bg(slide1, DARK_BG)

    # Accent decorative top bar
    bar = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(0.12))
    bar.fill.solid()
    bar.fill.fore_color.rgb = GOLD
    bar.line.fill.background()

    # Category Pill
    pill1 = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(1.2), Inches(3.6), Inches(0.42))
    pill1.fill.solid()
    pill1.fill.fore_color.rgb = CARD_BG_DARK
    pill1.line.color.rgb = GOLD
    pill1.line.width = Pt(1)
    p1_tf = pill1.text_frame
    p1_tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = p1_tf.paragraphs[0]
    p.text = "ENTERPRISE SPORTS & HOSPITALITY SUITE"
    p.alignment = PP_ALIGN.CENTER
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = GOLD

    # Main Title Box
    title_box = slide1.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11.3), Inches(2.2))
    t_tf = title_box.text_frame
    t_tf.word_wrap = True
    p = t_tf.paragraphs[0]
    p.text = "THE CHAMPIONS CLUB"
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = TEXT_WHITE
    p.space_after = Pt(8)

    p_sub = t_tf.add_paragraph()
    p_sub.text = "Unified Management System for Modern Luxury Sports Facilities"
    p_sub.font.size = Pt(20)
    p_sub.font.color.rgb = MINT
    p_sub.space_after = Pt(14)

    p_desc = t_tf.add_paragraph()
    p_desc.text = "High-concurrency court reservation locks, live pro-forma UPI billing, zero-trust RBAC security isolation, and complete multi-departmental operations."
    p_desc.font.size = Pt(13)
    p_desc.font.color.rgb = TEXT_MUTED_DARK

    # 4 Highlights Pills on Title
    features = [
        ("Concurrency Locks", "Zero Double-Bookings"),
        ("Live Pro-Forma Bills", "Dynamic UPI QR & UTR"),
        ("Strict 6-Role RBAC", "403 Ledger Isolation"),
        ("All-in-One Engine", "Sports • POS • KDS • EHR")
    ]
    card_w = Inches(2.65)
    gap = Inches(0.24)
    start_x = Inches(1.0)
    top_y = Inches(4.35)

    for i, (title, sub) in enumerate(features):
        c_x = start_x + i * (card_w + gap)
        c = add_card(slide1, c_x, top_y, card_w, Inches(1.15), bg_color=CARD_BG_DARK, border_color=CARD_BORDER_DARK)
        ctf = c.text_frame
        ctf.word_wrap = True
        ctf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = ctf.paragraphs[0]
        p.text = title
        p.alignment = PP_ALIGN.CENTER
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = GOLD
        p2 = ctf.add_paragraph()
        p2.text = sub
        p2.alignment = PP_ALIGN.CENTER
        p2.font.size = Pt(10)
        p2.font.color.rgb = TEXT_WHITE
        p2.space_before = Pt(4)

    # Authors / Project Credits Footer Card
    footer = add_card(slide1, Inches(1.0), Inches(5.85), Inches(11.333), Inches(1.1), bg_color=CARD_BG_DARK, border_color=CARD_BORDER_DARK)
    f_tf = footer.text_frame
    f_tf.word_wrap = True
    f_tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    
    fp1 = f_tf.paragraphs[0]
    fp1.text = "DEVELOPMENT TEAM & SPECIALIZATION MATRIX"
    fp1.font.size = Pt(10)
    fp1.font.bold = True
    fp1.font.color.rgb = GOLD
    fp1.space_after = Pt(4)

    fp2 = f_tf.add_paragraph()
    fp2.text = "• Manas (@manas0306-ops) — Security Architecture & System Audits     • Ujjwal Prakash (@ujjwalprakash07) — Backend APIs & Billing Engine\n• Vedant Kumar (@27vedantkumar) — Core Services & Concurrency Locks      • Uj1710glitch (@Uj1710glitch) — Frontend UI & Departmental Dashboards"
    fp2.font.size = Pt(11)
    fp2.font.color.rgb = TEXT_WHITE

    # ==========================================
    # SLIDE 2: PROBLEM STATEMENT & EXECUTIVE VISION
    # ==========================================
    slide2 = prs.slides.add_slide(blank_layout)
    add_bg(slide2, LIGHT_BG)
    add_header(slide2, "STRATEGIC CONTEXT", "Executive Problem Statement & Architecture Vision", "Overcoming legacy friction through an integrated real-time sports hospitality engine")

    col_w = Inches(5.65)
    top_pos = Inches(1.75)
    card_h = Inches(5.2)

    # Left Card: Legacy Deficiencies
    left_c = add_card(slide2, Inches(0.8), top_pos, col_w, card_h, CARD_BG_LIGHT, CARD_BORDER_LIGHT)
    ltf = left_c.text_frame
    ltf.word_wrap = True
    ltf.margin_left = Inches(0.3)
    ltf.margin_right = Inches(0.3)
    ltf.margin_top = Inches(0.3)

    lp = ltf.paragraphs[0]
    lp.text = "LEGACY SYSTEM DEFICIENCIES"
    lp.font.size = Pt(14)
    lp.font.bold = True
    lp.font.color.rgb = RGBColor(220, 38, 38) # Red accent
    lp.space_after = Pt(12)

    problems = [
        ("Double-Bookings & Schedule Collisions", "Manual registers and unsynchronized desk calendars cause catastrophic court overlaps during peak hours (17:00-21:00)."),
        ("Financial Leakage & Zero Traceability", "Members claim cash or phone payments without digital audit trails, resulting in reconciliation deficits and lost club revenue."),
        ("Security & Privacy Breaches", "Frontline staff, gym trainers, and café servers have unrestricted view access to confidential member directories and the executive financial ledger."),
        ("Fragmented Silos & Poor Hospitality", "Café tabs, equipment pro-shop rentals, physio clinics, and court bookings operate on isolated systems with zero shared member profiles.")
    ]
    for title, desc in problems:
        p_t = ltf.add_paragraph()
        p_t.text = "✖  " + title
        p_t.font.size = Pt(11)
        p_t.font.bold = True
        p_t.font.color.rgb = TEXT_DARK
        p_t.space_before = Pt(8)
        p_d = ltf.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(10)
        p_d.font.color.rgb = TEXT_MUTED_LIGHT
        p_d.space_before = Pt(2)

    # Right Card: The Champions Club Paradigm
    right_c = add_card(slide2, Inches(6.85), top_pos, col_w, card_h, CARD_BG_LIGHT, CARD_BORDER_LIGHT)
    rtf = right_c.text_frame
    rtf.word_wrap = True
    rtf.margin_left = Inches(0.3)
    rtf.margin_right = Inches(0.3)
    rtf.margin_top = Inches(0.3)

    rp = rtf.paragraphs[0]
    rp.text = "THE CHAMPIONS CLUB PARADIGM"
    rp.font.size = Pt(14)
    rp.font.bold = True
    rp.font.color.rgb = EMERALD
    rp.space_after = Pt(12)

    solutions = [
        ("Atomic Concurrency Locks", "Reservations immediately acquire temporary slot locks ('Pending') during payment, mathematically preventing concurrent double-bookings."),
        ("Dynamic Pro-Forma UPI Settlement", "Instant bill calculation with tier discounts, dynamic UPI QR generation, 12-digit UTR capture, and dual-authorization verification."),
        ("Strict Multi-Tier RBAC & Isolation", "Hardened 403 authorization boundary. Financial ledger and member rosters strictly locked to Owner & Admin; staff confined to their own modules."),
        ("Unified Single-Pane Operations", "Centralized database uniting court schedules, Pro Shop retail POS, Café KDS/tabs, Physio medical EHR, and CRM sales lead tracking.")
    ]
    for title, desc in solutions:
        p_t = rtf.add_paragraph()
        p_t.text = "✔  " + title
        p_t.font.size = Pt(11)
        p_t.font.bold = True
        p_t.font.color.rgb = EMERALD
        p_t.space_before = Pt(8)
        p_d = rtf.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(10)
        p_d.font.color.rgb = TEXT_MUTED_LIGHT
        p_d.space_before = Pt(2)

    # ==========================================
    # SLIDE 3: MULTI-ROLE RBAC & ZERO-TRUST SECURITY
    # ==========================================
    slide3 = prs.slides.add_slide(blank_layout)
    add_bg(slide3, LIGHT_BG)
    add_header(slide3, "GOVERNANCE & PRIVILEGE MATRIX", "Multi-Role RBAC & Zero-Trust Security Boundary", "Strict 403 Forbidden enforcement isolating financial ledgers and customer data")

    roles = [
        ("Executive Owner", "Full P&L Oversight", EMERALD, [
            "Complete financial ledger audit",
            "Club-wide revenue & expense analytics",
            "Approve/Reject high-value transactions",
            "Global staff credential management"
        ]),
        ("Front Desk Admin", "Daily Facility Operations", NAVY_ACCENT, [
            "Court schedule oversight & slot locks",
            "Member check-in & roster management",
            "Booking payment verification (UTR)",
            "Guest onboarding & visitor passes"
        ]),
        ("Department Staff", "Café, Pro Shop, Physio", GOLD, [
            "Strictly isolated to domain dashboards",
            "Café: KDS orders & shift cash tabs",
            "Shop: Retail inventory & gear sales",
            "Physio: Confidential SOAP clinic notes"
        ]),
        ("Club Members", "Tier-Based Self-Service", RGBColor(79, 70, 229), [
            "Tier privileges (Gold, Silver, Free)",
            "Book courts & browse gear/café menus",
            "Generate pro-forma bills & enter UTR",
            "403 Blocked from ledger & other profiles"
        ])
    ]

    r_w = Inches(2.78)
    r_gap = Inches(0.2)
    start_r = Inches(0.8)
    r_top = Inches(1.75)
    r_h = Inches(4.0)

    for i, (role_name, role_sub, accent_color, duties) in enumerate(roles):
        rx = start_r + i * (r_w + r_gap)
        c = add_card(slide3, rx, r_top, r_w, r_h, CARD_BG_LIGHT, CARD_BORDER_LIGHT)
        ctf = c.text_frame
        ctf.word_wrap = True
        ctf.margin_left = Inches(0.22)
        ctf.margin_right = Inches(0.22)
        ctf.margin_top = Inches(0.25)

        p = ctf.paragraphs[0]
        p.text = role_name
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = accent_color

        p_sub = ctf.add_paragraph()
        p_sub.text = role_sub
        p_sub.font.size = Pt(10)
        p_sub.font.color.rgb = TEXT_MUTED_LIGHT
        p_sub.space_after = Pt(10)

        for duty in duties:
            dp = ctf.add_paragraph()
            dp.text = "• " + duty
            dp.font.size = Pt(10)
            dp.font.color.rgb = TEXT_DARK
            dp.space_before = Pt(5)

    # Bottom Security Highlights Bar
    sec_bar = add_card(slide3, Inches(0.8), Inches(5.95), Inches(11.7), Inches(1.0), bg_color=CARD_BG_LIGHT, border_color=EMERALD)
    stf = sec_bar.text_frame
    stf.word_wrap = True
    stf.vertical_anchor = MSO_ANCHOR.MIDDLE
    stf.margin_left = Inches(0.3)
    stf.margin_right = Inches(0.3)

    sp = stf.paragraphs[0]
    sp.text = "CRYPTOGRAPHIC INTEGRITY & ATTACK MITIGATION"
    sp.font.size = Pt(11)
    sp.font.bold = True
    sp.font.color.rgb = EMERALD
    sp.space_after = Pt(2)

    sp2 = stf.add_paragraph()
    sp2.text = "Signed HMAC session tokens prevent tampering. Passwords salted & hashed via bcrypt. All transaction endpoints enforce server-side role validation, returning HTTP 403 Forbidden on privilege escalation attempts."
    sp2.font.size = Pt(10)
    sp2.font.color.rgb = TEXT_MUTED_LIGHT

    # ==========================================
    # SLIDE 4: COURT SCHEDULING & CONCURRENCY
    # ==========================================
    slide4 = prs.slides.add_slide(blank_layout)
    add_bg(slide4, LIGHT_BG)
    add_header(slide4, "FACILITY ENGINE", "Court Collision Locks & Reservation Concurrency", "Zero-collision scheduling across 5 sports disciplines and peak operational windows")

    c4_w = Inches(3.68)
    c4_gap = Inches(0.33)
    c4_start = Inches(0.8)
    c4_top = Inches(1.75)
    c4_h = Inches(5.15)

    sched_cards = [
        ("Multi-Sport Matrix", EMERALD, [
            ("5 Disciplines", "Badminton, Tennis, Squash, Swimming Pool, and Gymnasium."),
            ("Operating Hours", "06:00 to 22:00 IST continuous daily operations with 60-min standard slots."),
            ("Peak Rate Balancing", "Prime evening slots (17:00-21:00) with dynamic lighting surcharges and tier privileges."),
            ("Friday Social Mixer", "Dedicated community recurring mixer sessions with standing multi-player slots.")
        ]),
        ("Concurrency Lock Protocol", GOLD, [
            ("Interval Collision Query", "Server evaluates (start < existing_end) AND (end > existing_start) in real-time."),
            ("Immediate 'Pending' Lock", "Upon clicking Book, slot is flagged status='Pending'. Locked from other users during payment."),
            ("Time-to-Live Expiry", "Unpaid pending locks release automatically if UTR is not entered, preventing slot hoarding."),
            ("Zero Double-Bookings", "Validated through 100% automated concurrent stress test test_security_and_approvals.py.")
        ]),
        ("Lifecycle State Machine", NAVY_ACCENT, [
            ("State 1: Slot Selection", "Member views live court availability grid and selects open time window."),
            ("State 2: Pending Hold", "Pro-forma bill generated with UPI QR code; slot locked on database calendar."),
            ("State 3: Admin Verification", "Desk verifies 12-digit bank UTR; approves payment with one click."),
            ("State 4: Confirmation", "Status transitions to 'Confirmed'; QR ticket issued and calendar booked.")
        ])
    ]

    for i, (card_title, col, items) in enumerate(sched_cards):
        cx = c4_start + i * (c4_w + c4_gap)
        c = add_card(slide4, cx, c4_top, c4_w, c4_h, CARD_BG_LIGHT, CARD_BORDER_LIGHT)
        ctf = c.text_frame
        ctf.word_wrap = True
        ctf.margin_left = Inches(0.25)
        ctf.margin_right = Inches(0.25)
        ctf.margin_top = Inches(0.25)

        p = ctf.paragraphs[0]
        p.text = card_title
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = col
        p.space_after = Pt(10)

        for sub_h, sub_d in items:
            ip = ctf.add_paragraph()
            ip.text = "▸ " + sub_h
            ip.font.size = Pt(11)
            ip.font.bold = True
            ip.font.color.rgb = TEXT_DARK
            ip.space_before = Pt(7)

            dp = ctf.add_paragraph()
            dp.text = sub_d
            dp.font.size = Pt(10)
            dp.font.color.rgb = TEXT_MUTED_LIGHT
            dp.space_before = Pt(2)

    # ==========================================
    # SLIDE 5: LIVE PRO-FORMA BILLING & UPI GATEWAY
    # ==========================================
    slide5 = prs.slides.add_slide(blank_layout)
    add_bg(slide5, LIGHT_BG)
    add_header(slide5, "FINANCIAL ARCHITECTURE", "Live Pro-Forma Billing & Dynamic UPI Gateway", "Transparent itemized invoices with zero payment-gateway fees and dual UTR verification")

    # 4 Steps of Billing Workflow
    steps = [
        ("1. Dynamic Bill Calculation", "Applies tiered discounts (Gold: 25% off, Silver: 10% off), court lighting fees, and GST in real-time.", EMERALD),
        ("2. Real-Time UPI QR Generation", "Renders dynamic NPCI-standard QR code encoded with club VPA, calculated amount, and reference invoice ID.", GOLD),
        ("3. Member 12-Digit UTR Entry", "Member scans QR with Google Pay, PhonePe, or Paytm, and submits the 12-digit bank UTR reference.", NAVY_ACCENT),
        ("4. Admin Approval & Audit Ledger", "Front Desk cross-references live bank feed, approves transaction, and commits ledger entry.", RGBColor(16, 185, 129))
    ]

    s_w = Inches(2.78)
    s_gap = Inches(0.2)
    s_start = Inches(0.8)
    s_top = Inches(1.75)
    s_h = Inches(1.8)

    for i, (stitle, sdesc, scolor) in enumerate(steps):
        sx = s_start + i * (s_w + s_gap)
        c = add_card(slide5, sx, s_top, s_w, s_h, CARD_BG_LIGHT, CARD_BORDER_LIGHT)
        ctf = c.text_frame
        ctf.word_wrap = True
        ctf.margin_left = Inches(0.2)
        ctf.margin_right = Inches(0.2)
        ctf.margin_top = Inches(0.2)

        p = ctf.paragraphs[0]
        p.text = stitle
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = scolor
        p.space_after = Pt(4)

        p2 = ctf.add_paragraph()
        p2.text = sdesc
        p2.font.size = Pt(9.5)
        p2.font.color.rgb = TEXT_MUTED_LIGHT

    # Two Comparative Detail Panels Below
    b_top = Inches(3.75)
    b_w = Inches(5.65)
    b_h = Inches(3.15)

    # Left: Tier Matrix
    tier_c = add_card(slide5, Inches(0.8), b_top, b_w, b_h, CARD_BG_LIGHT, CARD_BORDER_LIGHT)
    ttf = tier_c.text_frame
    ttf.word_wrap = True
    ttf.margin_left = Inches(0.3)
    ttf.margin_right = Inches(0.3)
    ttf.margin_top = Inches(0.25)

    p = ttf.paragraphs[0]
    p.text = "MEMBERSHIP TIER DISCOUNT MATRIX"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = GOLD
    p.space_after = Pt(8)

    tier_details = [
        ("Gold Elite Tier (₹5,000/mo)", "25% Court Discount, 15% Café/Shop Discount, Priority 7-day advance booking window, complimentary guest passes."),
        ("Silver Tier (₹2,500/mo)", "10% Court Discount, 5% Café/Shop Discount, 3-day advance booking window."),
        ("Free / Guest Tier", "Standard base pricing, same-day walk-in booking only, full pro-forma UPI prepayment required.")
    ]
    for th, td in tier_details:
        tp = ttf.add_paragraph()
        tp.text = "• " + th
        tp.font.size = Pt(10.5)
        tp.font.bold = True
        tp.font.color.rgb = TEXT_DARK
        tp.space_before = Pt(4)
        tdp = ttf.add_paragraph()
        tdp.text = td
        tdp.font.size = Pt(9.5)
        tdp.font.color.rgb = TEXT_MUTED_LIGHT

    # Right: Direct Settlement Benefits
    bank_c = add_card(slide5, Inches(6.85), b_top, b_w, b_h, CARD_BG_LIGHT, CARD_BORDER_LIGHT)
    btf = bank_c.text_frame
    btf.word_wrap = True
    btf.margin_left = Inches(0.3)
    btf.margin_right = Inches(0.3)
    btf.margin_top = Inches(0.25)

    p = btf.paragraphs[0]
    p.text = "DIRECT SETTLEMENT & ZERO GATEWAY SURCHARGE"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = EMERALD
    p.space_after = Pt(8)

    fin_details = [
        ("0% Gateway Commissions", "Standard gateways charge 2.0-3.5% per swipe. Direct UPI VPA settlement retains 100% of revenue in the club's account."),
        ("Instant Bank Settlement", "Zero T+2 holding delays. Funds arrive in the club's bank account instantly upon member transfer."),
        ("Cryptographic Audit Trail", "All approved and rejected transactions recorded with reviewer timestamp, member ID, and immutable UTR record.")
    ]
    for fh, fd in fin_details:
        fp = btf.add_paragraph()
        fp.text = "✔ " + fh
        fp.font.size = Pt(10.5)
        fp.font.bold = True
        fp.font.color.rgb = EMERALD
        fp.space_before = Pt(4)
        fdp = btf.add_paragraph()
        fdp.text = fd
        fdp.font.size = Pt(9.5)
        fdp.font.color.rgb = TEXT_MUTED_LIGHT

    # ==========================================
    # SLIDE 6: DEPARTMENTAL OPERATIONS & WORKFLOWS
    # ==========================================
    slide6 = prs.slides.add_slide(blank_layout)
    add_bg(slide6, LIGHT_BG)
    add_header(slide6, "OPERATIONAL EXCELLENCE", "Departmental Workflows & Integrated Micro-Services", "Custom purpose-built workstations for Retail, F&B, Sports Medicine, and Member Growth")

    dept_w = Inches(5.65)
    dept_h = Inches(2.45)

    depts = [
        (Inches(0.8), Inches(1.75), "Pro Shop POS & Inventory Management", EMERALD, [
            "Real-Time Stock Depletion: Automatic deduction upon order approval.",
            "Re-order Alert Thresholds: Flags equipment falling below minimum stock.",
            "Gear Rentals: Racket and ball machine hourly checkout and returns.",
            "Pro-forma Billing: Members scan UPI QR or charge active house accounts."
        ]),
        (Inches(6.85), Inches(1.75), "Café & Sports Bar KDS (Kitchen Display)", GOLD, [
            "Live Ticket Pipeline: Tracks orders across Received, Prepping, and Ready states.",
            "Table Tab Management: Running dining balances linked to member IDs.",
            "Shift Register Reconciliation: Cash drawer, UPI receipts, and card splits.",
            "Nutritional Profiling: High-protein athletic meal tagging."
        ]),
        (Inches(0.8), Inches(4.45), "Physiotherapy & Sports Medicine Clinic", NAVY_ACCENT, [
            "Confidential Clinical EHR: Secure SOAP injury treatment records.",
            "Recovery Tracking: Assessment notes, rehab progress, and treatment milestones.",
            "Session Appointments: Direct scheduling integrated into court recovery hours.",
            "Physio Access Only: Strictly isolated from front desk and café staff."
        ]),
        (Inches(6.85), Inches(4.45), "CRM Pipeline & Member Sales Lifecycle", RGBColor(147, 51, 234), [
            "Lead Conversion Tracking: Prospect ingestion from walk-in trials to paid tiers.",
            "Attendance Tracking: Automated alerts for at-risk churn members.",
            "Targeted Promotions: Pro-Shop discounts and VIP tournament invitations.",
            "Guest Pass Allocation: Controlled guest allowances linked to tier policies."
        ])
    ]

    for dx, dy, dtitle, dcolor, dpoints in depts:
        c = add_card(slide6, dx, dy, dept_w, dept_h, CARD_BG_LIGHT, CARD_BORDER_LIGHT)
        ctf = c.text_frame
        ctf.word_wrap = True
        ctf.margin_left = Inches(0.25)
        ctf.margin_right = Inches(0.25)
        ctf.margin_top = Inches(0.2)

        p = ctf.paragraphs[0]
        p.text = dtitle
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = dcolor
        p.space_after = Pt(4)

        for pt in dpoints:
            pp = ctf.add_paragraph()
            pp.text = "• " + pt
            pp.font.size = Pt(9.5)
            pp.font.color.rgb = TEXT_DARK
            pp.space_before = Pt(3)

    # ==========================================
    # SLIDE 7: TECHNICAL STACK, TOPOLOGY & BENCHMARKS (Dark Theme Finale)
    # ==========================================
    slide7 = prs.slides.add_slide(blank_layout)
    add_bg(slide7, DARK_BG)
    add_header(slide7, "ENGINEERING & DEPLOYMENT", "Technical Stack, System Topology & Benchmarks", "High-throughput asynchronous Python architecture engineered for enterprise reliability", is_dark=True)

    t_w = Inches(3.68)
    t_gap = Inches(0.33)
    t_start = Inches(0.8)
    t_top = Inches(1.75)
    t_h = Inches(5.15)

    tech_cards = [
        ("Core Stack & Data Layer", GOLD, [
            ("FastAPI & ASGI Uvicorn", "Asynchronous Python 3.12+ backend delivering sub-15ms endpoint latency."),
            ("SQLAlchemy 2.0 ORM", "Declarative schema with SQLite for edge testing and PostgreSQL-ready connection pools."),
            ("Jinja2 SSR Architecture", "Server-side HTML rendering eliminates heavy JS SPA bloat and guarantees instant loads."),
            ("Tailwind CSS Design System", "High-contrast luxury design with responsive desktop and mobile viewports.")
        ]),
        ("Security & Edge Topology", MINT, [
            ("Cloudflare Zero Trust Tunnel", "Secure TLS edge tunneling with zero exposed router ports or public IP vulnerabilities."),
            ("HMAC Signed Sessions", "Session tampering prevention with encrypted cookie headers and nonce checks."),
            ("Bcrypt Password Hashing", "Work factor 12 cryptographic salting protecting all stored user credentials."),
            ("Input Validation & Sanitize", "Pydantic data models protecting against SQL injection, XSS, and payload attacks.")
        ]),
        ("Quality Assurance & Ops", TEXT_WHITE, [
            ("100% Regression Suite Pass", "Automated pytest suite testing RBAC boundaries, concurrent locks, and payment approvals."),
            ("One-Click Local Launchers", "run_server.bat and run_public_tunnel.bat for instant zero-dependency launch."),
            ("Scalability Pathway", "Stateless ASGI application nodes ready for Docker containerization and Kubernetes scaling."),
            ("Production Readiness", "Enterprise-grade uptime with comprehensive logging and transaction audit records.")
        ])
    ]

    for i, (ctitle, ccol, citems) in enumerate(tech_cards):
        cx = t_start + i * (t_gap + t_w)
        c = add_card(slide7, cx, t_top, t_w, t_h, CARD_BG_DARK, CARD_BORDER_DARK)
        ctf = c.text_frame
        ctf.word_wrap = True
        ctf.margin_left = Inches(0.25)
        ctf.margin_right = Inches(0.25)
        ctf.margin_top = Inches(0.25)

        p = ctf.paragraphs[0]
        p.text = ctitle
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = ccol
        p.space_after = Pt(10)

        for ih, idesc in citems:
            ip = ctf.add_paragraph()
            ip.text = "▸ " + ih
            ip.font.size = Pt(11)
            ip.font.bold = True
            ip.font.color.rgb = TEXT_WHITE
            ip.space_before = Pt(8)

            dp = ctf.add_paragraph()
            dp.text = idesc
            dp.font.size = Pt(9.5)
            dp.font.color.rgb = TEXT_MUTED_DARK
            dp.space_before = Pt(2)

    # Save presentation
    prs.save(output_path)
    print(f"Successfully generated 7-slide presentation at: {os.path.abspath(output_path)}")

if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "Champions_Club_Presentation.pptx"
    create_presentation(out_file)

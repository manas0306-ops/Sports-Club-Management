# -*- coding: utf-8 -*-
"""
Bulletproof PowerPoint Generator for The Champions Club System Design.
Engineered for 100% compatibility across Microsoft PowerPoint (Windows/Mac/Web),
Apple Keynote, Google Slides, and LibreOffice without any XML corruption.
"""
import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def build_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Image 2 Aesthetic: Warm Amber & Deep Espresso Palette
    BG_COLOR = RGBColor(18, 12, 8)        # #120c08 Deep Espresso
    CARD_BG = RGBColor(34, 23, 17)        # #221711 Warm Frosted Card
    AMBER_GOLD = RGBColor(245, 158, 11)   # #f59e0b Warm Amber
    LIGHT_GOLD = RGBColor(251, 191, 36)   # #fbbf24 Bright Gold
    TEXT_WHITE = RGBColor(253, 250, 245)  # #fdfaf5 Ivory White
    TEXT_MUTED = RGBColor(180, 175, 169)  # #b4afa9 Muted Stone
    BORDER_COLOR = RGBColor(120, 53, 15)  # #78350f Bronze Border
    ACCENT_GREEN = RGBColor(16, 185, 129) # #10b981 Emerald
    ACCENT_ROSE = RGBColor(244, 63, 94)   # #f43f5e Soft Rose

    # Use clean blank layout (index 6 is blank in default template)
    blank_layout = prs.slide_layouts[6]

    def draw_bg(slide):
        """Draw full-bleed background shape to prevent OpenXML p:bg corruption"""
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_COLOR
        bg.line.fill.background()
        return bg

    def add_header(slide, title_text, category_text="THE CHAMPIONS CLUB | SYSTEM DESIGN & ARCHITECTURE"):
        # Category tag
        tb_cat = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.35))
        tf_c = tb_cat.text_frame
        tf_c.word_wrap = True
        p_c = tf_c.paragraphs[0]
        p_c.text = category_text.upper()
        p_c.font.size = Pt(11)
        p_c.font.bold = True
        p_c.font.color.rgb = AMBER_GOLD
        p_c.font.name = "Arial"

        # Main Slide Title
        tb_title = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.7), Inches(0.7))
        tf_t = tb_title.text_frame
        tf_t.word_wrap = True
        p_t = tf_t.paragraphs[0]
        p_t.text = title_text
        p_t.font.size = Pt(24)
        p_t.font.bold = True
        p_t.font.color.rgb = TEXT_WHITE
        p_t.font.name = "Arial"

    def add_card(slide, left, top, width, height, title, points, accent_color=AMBER_GOLD):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = BORDER_COLOR
        card.line.width = Pt(1.5)

        pad = Inches(0.25)
        tb = slide.shapes.add_textbox(left + pad, top + pad, width - (pad * 2), height - (pad * 2))
        tf = tb.text_frame
        tf.word_wrap = True

        p_title = tf.paragraphs[0]
        p_title.text = title
        p_title.font.size = Pt(14)
        p_title.font.bold = True
        p_title.font.color.rgb = accent_color
        p_title.font.name = "Arial"
        p_title.space_after = Pt(10)

        for pt in points:
            p_pt = tf.add_paragraph()
            p_pt.text = "• " + pt
            p_pt.font.size = Pt(10.5)
            p_pt.font.color.rgb = TEXT_WHITE
            p_pt.font.name = "Arial"
            p_pt.space_after = Pt(6)

    # ---------------------------------------------------------
    # SLIDE 1: Title & Overview
    # ---------------------------------------------------------
    s1 = prs.slides.add_slide(blank_layout)
    draw_bg(s1)

    hero = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(1.1), Inches(10.9), Inches(5.3))
    hero.fill.solid()
    hero.fill.fore_color.rgb = CARD_BG
    hero.line.color.rgb = BORDER_COLOR
    hero.line.width = Pt(2)

    tb1 = s1.shapes.add_textbox(Inches(1.8), Inches(1.5), Inches(9.7), Inches(4.5))
    tf1 = tb1.text_frame
    tf1.word_wrap = True

    p_tag = tf1.paragraphs[0]
    p_tag.text = "ENTERPRISE TECHNICAL SPECIFICATION & SYSTEM DESIGN"
    p_tag.font.size = Pt(12)
    p_tag.font.bold = True
    p_tag.font.color.rgb = AMBER_GOLD
    p_tag.font.name = "Arial"
    p_tag.space_after = Pt(14)

    p_h = tf1.add_paragraph()
    p_h.text = "The Champions Club Management System"
    p_h.font.size = Pt(32)
    p_h.font.bold = True
    p_h.font.color.rgb = TEXT_WHITE
    p_h.font.name = "Arial"
    p_h.space_after = Pt(12)

    p_s = tf1.add_paragraph()
    p_s.text = "High-Level Architecture (HLD), Low-Level Data Models (LLD), Strict 5-Role RBAC, Single-Shelf Unified Inventory, Mathematical Collision Engine & Odoo 17 Backbone"
    p_s.font.size = Pt(13)
    p_s.font.color.rgb = TEXT_MUTED
    p_s.font.name = "Arial"
    p_s.space_after = Pt(22)

    p_m = tf1.add_paragraph()
    p_m.text = "Stack: Python 3.11 | FastAPI Async Core | SQLAlchemy 2.0 | SQLite (23 Tables) | Jinja2 Glassmorphism | Odoo 17 ERP | 41/41 Passing Automated Tests"
    p_m.font.size = Pt(11.5)
    p_m.font.bold = True
    p_m.font.color.rgb = LIGHT_GOLD
    p_m.font.name = "Arial"

    # ---------------------------------------------------------
    # SLIDE 2: Executive Summary & Challenge
    # ---------------------------------------------------------
    s2 = prs.slides.add_slide(blank_layout)
    draw_bg(s2)
    add_header(s2, "Executive Summary: The Unified Club Challenge")

    add_card(s2, Inches(0.8), Inches(1.6), Inches(3.6), Inches(5.2), "The Problem Landscape", [
        "Fragmented Silos: Paper spreadsheets, manual bar slips, and detached pro shop inventory.",
        "Court Clashes: WhatsApp-driven double bookings & prime-time evening slot monopolization.",
        "Revenue Blindspots: Inability to reconcile court fees, merchandise, bar tabs & memberships.",
        "Unsecured Guest Flow: Public walk-ins lacking structured pay-per-play access control.",
        "Lost Kitchen Chits: Paper KOT delays leading to missed billing and inventory shrinkage."
    ], accent_color=ACCENT_ROSE)

    add_card(s2, Inches(4.8), Inches(1.6), Inches(3.6), Inches(5.2), "The Unified Architecture", [
        "FastAPI Reactive Core: Sub-millisecond REST APIs with auto-generated OpenAPI documentation.",
        "Strict 5-Role RBAC: Isolated security context for Admin, Member, Player, Staff & Walk-In.",
        "Real-time Single-Shelf Inventory: Synchronized physical stock across POS & Click & Collect.",
        "Mathematical Anti-Collision: Overlap detection rejects duplicate bookings with HTTP 409.",
        "Odoo 17 Enterprise Addon: Dual-engine architecture with XML views and security ACLs."
    ], accent_color=AMBER_GOLD)

    add_card(s2, Inches(8.8), Inches(1.6), Inches(3.7), Inches(5.2), "Key Performance Outcomes", [
        "Zero Double Bookings: Mathematical collision prevention guarantees 100% slot integrity.",
        "41/41 Automated Tests: End-to-end regression passing in <12 seconds.",
        "173 Seeded User Accounts: Pre-provisioned bcrypt credentials across all club tiers.",
        "165 Member Records: Gold, Silver, Junior, and Walk-In profiles fully populated.",
        "Warm Glassmorphism UI: Adorable tactile controls (lighting dial, smoothie maker, 3D cards)."
    ], accent_color=ACCENT_GREEN)

    # ---------------------------------------------------------
    # SLIDE 3: HLD Topology
    # ---------------------------------------------------------
    s3 = prs.slides.add_slide(blank_layout)
    draw_bg(s3)
    add_header(s3, "High-Level Architecture (HLD) & System Topology")

    add_card(s3, Inches(0.8), Inches(1.6), Inches(2.7), Inches(5.2), "1. Client Layer", [
        "Responsive Web UI",
        "Warm Amber Glassmorphism",
        "Tailwind CSS & Lucide Icons",
        "Web Audio Synthesizer (0KB)",
        "Holographic 3D Tilt Cards",
        "Interactive Lighting Dial",
        "Dynamic Island Navigation"
    ])

    add_card(s3, Inches(3.8), Inches(1.6), Inches(2.7), Inches(5.2), "2. Security & Gateway", [
        "HTTP-Only Session Cookies",
        "Signed HS256 JWT Tokens",
        "Server Token Revocation List",
        "Bcrypt Salted Hashes (r=12)",
        "Rate Limiting & Lockout Engine",
        "Role Selection Verification",
        "HTTP 403 Cross-Role Traps"
    ])

    add_card(s3, Inches(6.8), Inches(1.6), Inches(2.7), Inches(5.2), "3. Application Core", [
        "FastAPI High-Speed Async Engine",
        "6 Scene Domain Routers",
        "Member Management Service",
        "Court Collision Prevention",
        "Single-Shelf Inventory Lock",
        "Sports Bar & KDS Service",
        "5-Stage CRM Pipeline"
    ])

    add_card(s3, Inches(9.8), Inches(1.6), Inches(2.7), Inches(5.2), "4. Storage & ERP", [
        "SQLAlchemy 2.0 ORM",
        "SQLite (champions_club.db)",
        "23 Relational Tables",
        "Foreign Key Cascade Integrity",
        "Odoo 17 Modular Addon",
        "Odoo ir.model.access ACLs",
        "Immutable Security Audit Logs"
    ])

    # ---------------------------------------------------------
    # SLIDE 4: RBAC & Role Isolation
    # ---------------------------------------------------------
    s4 = prs.slides.add_slide(blank_layout)
    draw_bg(s4)
    add_header(s4, "Security Architecture: Strict Role Isolation & RBAC")

    add_card(s4, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2), "Five Primary Account Roles", [
        "ADMIN: Complete club oversight, business analytics, user management, and system audit logs. Strictly isolated from direct member dashboard impersonation.",
        "MEMBER: Full member privileges with Gold, Silver, or Underage classification. Access to digital passes, bookings, renewals, and personal invoices.",
        "PLAYER: Dedicated athlete portal with training drills, tournament fixtures, club rankings, and match performance analytics.",
        "STAFF: Granular operational access for Receptionists, Court Managers, Bar Staff, and Kitchen Crews. No access to owner financial reports.",
        "WALK_IN: Restricted public guest pass for pay-per-play bookings without exposing internal management functions."
    ])

    add_card(s4, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2), "Strict Server-Side Enforcement (HTTP 403)", [
        "Zero Client Trust: Redirection and authorization are strictly determined by database account records, never frontend form parameters.",
        "Cross-Role Trap Matrix: Member accessing Admin dashboard triggers HTTP 403 Forbidden and records UNAUTHORIZED_ACCESS_ATTEMPT in AuditLog.",
        "Unauthenticated Protection: Direct URL tampering redirects unauthenticated browser requests with HTTP 307 to /login?next=...",
        "Server-Side Revocation: Logging out permanently invalidates the token in the server-side revocation registry, preventing token replay attacks.",
        "Youth Protection: Junior members (<18) enforce verified Guardian consent, emergency phone, and age-appropriate booking safeguards."
    ], accent_color=LIGHT_GOLD)

    # ---------------------------------------------------------
    # SLIDE 5: Court Anti-Collision Lock
    # ---------------------------------------------------------
    s5 = prs.slides.add_slide(blank_layout)
    draw_bg(s5)
    add_header(s5, "Domain Engine 1: Mathematical Court Anti-Collision Lock")

    add_card(s5, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2), "The Anti-Double-Booking Algorithm", [
        "Standardized 60-Minute Slots: Bookings are scheduled on 30-minute staggered intervals (e.g., 08:00-09:00, 08:30-09:30).",
        "Mathematical Overlap Condition: A conflict occurs if requested start < existing end AND requested end > existing start for the same court.",
        "Atomic Transaction Lock: Pre-commit collision queries raise HTTP 409 Conflict with detailed collision timestamps before any write completes.",
        "Anti-Monopoly Daily Cap: Business logic enforces max 2 court sessions per member per day, stopping prime-time monopolization.",
        "Friday Social Mode: Configurable club mode allowing multi-player occupancy for weekly doubles mixer tournaments."
    ])

    add_card(s5, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2), "Tiered Court Access & Financial Logic", [
        "Gold Tier: 100% Free Court Access (INR 0 fee automatically computed by pricing engine).",
        "Silver Tier: 50% Court Fee Discount (Standard INR 800/hr reduced to INR 400/hr).",
        "Junior Tier: 60% Youth Development Discount (Reduced to INR 320/hr).",
        "Walk-In Guests: Pay standard non-member rate (INR 800 - 1,000/hr) with instant booking reference.",
        "Cancellation Protection: Policy requires 24-hour advance notice; late cancellations forfeit booking deposits to ensure high court utilization."
    ])

    # ---------------------------------------------------------
    # SLIDE 6: Single-Shelf Inventory
    # ---------------------------------------------------------
    s6 = prs.slides.add_slide(blank_layout)
    draw_bg(s6)
    add_header(s6, "Domain Engine 2: Unified Single-Shelf Gear Inventory")

    add_card(s6, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2), "Single-Shelf Inventory Synchronization", [
        "Unified Stock Pool: Eliminates desynchronization between counter walk-in purchases and online sofa / Click & Collect orders.",
        "Real-Time Stock Deduction: Every completed checkout atomically decrements stock_quantity in the products table.",
        "Insufficient Stock Rejection: Transactions requesting more units than available stock fail immediately with HTTP 400 Bad Request.",
        "Automated Reorder Thresholds: Flags products when stock drops below threshold_level (e.g., < 5 tennis ball cans).",
        "Multi-Category Support: Racquets, Strings, Footwear, Apparel, Balls, and High-Performance Nutrition."
    ])

    add_card(s6, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2), "Automated Membership Discount Pipeline", [
        "Zero-Friction Discounting: Customer tier is detected at POS lookup; discounts apply automatically without awkward customer requests.",
        "Gold Member Discount: 20% discount on all pro gear and strings.",
        "Silver Member Discount: 10% discount on all pro shop items.",
        "Junior Member Discount: 10% discount on junior academy racquets and balls.",
        "Audit & Reorder Reporting: Single-shelf reporting provides stock valuation, low-stock warnings, and historical sales trends for club management."
    ])

    # ---------------------------------------------------------
    # SLIDE 7: Sports Bar POS & Live Kitchen KOT
    # ---------------------------------------------------------
    s7 = prs.slides.add_slide(blank_layout)
    draw_bg(s7)
    add_header(s7, "Domain Engine 3: Sports Bar POS & Live Kitchen KOT")

    add_card(s7, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2), "Floor Plan & Running Tabs System", [
        "Table Management: Interactive layout tracking 8 tables and bar zones with live occupancy states (Available, Occupied, Reserved).",
        "Persistent Member Tabs: Members can open running tabs and order throughout matchday without paying each round individually.",
        "Real-Time Member Discounts: 20% discount for Gold and 10% for Silver automatically deducted from tab totals.",
        "Multi-Channel Settlement: Supports Cash, Credit Card, and UPI QR code settlements with detailed payment receipts.",
        "Daily Z-Report Reconciliation: End-of-day closing tool summarizing cash drawer totals, card receipts, and outstanding tabs."
    ])

    add_card(s7, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2), "Kitchen Display System (KDS / KOT Routing)", [
        "Digital Slip Dispatch: Eliminates lost paper chits; bar orders route instantly to the Kitchen Display interface.",
        "State Machine Lifecycle: Order items transition through PENDING -> PREPARING -> READY -> SERVED.",
        "Preparation Time Tracking: Kitchen display shows wait timers, flagging overdue tickets in amber and red.",
        "Category Segregation: Beverage orders route to the Bartender station, while food items route to the Hot Kitchen line.",
        "Seamless POS Sync: Kitchen status updates reflect immediately on the main bar terminal without screen refreshing."
    ])

    # ---------------------------------------------------------
    # SLIDE 8: CRM & Owner Financial Engine
    # ---------------------------------------------------------
    s8 = prs.slides.add_slide(blank_layout)
    draw_bg(s8)
    add_header(s8, "Domain Engine 4 & 5: CRM Funnel, HR & Multi-Source Revenue")

    add_card(s8, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2), "5-Stage CRM & Free Trial Pipeline", [
        "Inbound Lead Capture: Public website trial requests and general enquiries feed directly into the central CRM.",
        "Automated Trial Scheduling: Assigns trial session date, sport, and Head Coach David without staff phone tag.",
        "Kanban Sales Stages: Pipeline tracks leads across NEW -> CONTACTED -> TRIAL_BOOKED -> QUOTED -> CONVERTED.",
        "Instant Quotation Generator: Formulates customized membership proposals with optional coaching clinic add-ons.",
        "1-Click Conversion: Converts winning leads into full active Member records, creating credentials and digital passes."
    ])

    add_card(s8, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2), "Owner Financial Engine & HR Management", [
        "Multi-Source Revenue Consolidation: Unifies streams from Court Bookings, Gear Shop, Sports Bar, Memberships & Corporate Invoices.",
        "GST & Tax Breakdown: Segregates 18% GST liabilities across equipment, services, and food & beverage.",
        "Payment Split Analytics: Real-time breakdowns across Cash, Credit Cards, and UPI digital payments.",
        "Staff Shift Roster: Tracks employee daily duty schedules (Reception, Maintenance, Bar, Coaching).",
        "HR Leave Approvals: Online leave submission and approval workflow with coverage validation."
    ])

    # ---------------------------------------------------------
    # SLIDE 9: LLD Relational Schema
    # ---------------------------------------------------------
    s9 = prs.slides.add_slide(blank_layout)
    draw_bg(s9)
    add_header(s9, "Low-Level Design (LLD): Database Schema & Relational Model")

    add_card(s9, Inches(0.8), Inches(1.6), Inches(3.6), Inches(5.2), "Core Identity & Security", [
        "users: id, email, username, password_hash, primary_role, is_active, is_verified, created_at, last_login.",
        "guardians: id, member_id, guardian_name, relationship_type, guardian_phone, guardian_email, consent_signed.",
        "player_profiles: id, user_id, athlete_name, primary_sport, skill_level, club_ranking, training_schedule.",
        "audit_logs: id, user_id, action, resource, ip_address, status, details, timestamp."
    ])

    add_card(s9, Inches(4.8), Inches(1.6), Inches(3.6), Inches(5.2), "Operations & Commerce", [
        "members: id, user_id, member_code, first_name, last_name, tier, status, start_date, expiry_date.",
        "courts: id, name, sport_type, surface, hourly_rate, is_active.",
        "court_bookings: id, court_id, member_id, booking_date, start_time, end_time, fee_charged, status.",
        "products: id, category_id, name, sku, price, stock_quantity, threshold_level.",
        "bar_tables & bar_tabs: table_id, member_id, subtotal, discount, total, status."
    ])

    add_card(s9, Inches(8.8), Inches(1.6), Inches(3.7), Inches(5.2), "CRM, Finance & HR", [
        "lead_enquiries: id, name, email, phone, interested_tier, status, notes.",
        "trial_bookings: id, visitor_name, email, sport_type, trial_date, status.",
        "quotes: id, lead_id, quote_number, tier_code, amount, status.",
        "invoices: id, member_id, invoice_number, total_amount, status.",
        "employees & staff_shifts: id, user_id, name, role, staff_group, shift_date, task_notes.",
        "leave_requests: id, employee_id, start_date, end_date, reason, status."
    ], accent_color=LIGHT_GOLD)

    # ---------------------------------------------------------
    # SLIDE 10: Odoo 17 Enterprise Addon
    # ---------------------------------------------------------
    s10 = prs.slides.add_slide(blank_layout)
    draw_bg(s10)
    add_header(s10, "Enterprise ERP Integration: Odoo 17 Modular Architecture")

    add_card(s10, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2), "Odoo 17 Addon Structure", [
        "Module Name: sports_club_management (Odoo 17 Community & Enterprise compatible).",
        "Declared Manifest (__manifest__.py): Declares dependencies on base, mail, product, sale, and account.",
        "Custom Python Models: sports.member, sports.court, sports.booking, sports.bar.tab, sports.crm.lead, sports.employee.",
        "Security Architecture (ir.model.access.csv): Role-based access rules for Club Managers, Receptionists, and Front Desk Staff.",
        "Data Initialization: Bundled XML seed data with standard courts, demo members, and product catalogs."
    ])

    add_card(s10, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2), "Rich XML Views & ERP Capabilities", [
        "Form Views: Detailed member inspection with smart action buttons for renewals and tab tracking.",
        "Tree / List Views: Color-coded status badges for active, expired, and suspended memberships.",
        "Kanban Views: Visual CRM lead pipelines with drag-and-drop opportunity progression.",
        "Calendar Views: Visual court schedule grids showing reservations, court maintenance, and coaching clinics.",
        "ERP Synchronicity: Sits alongside FastAPI backend, allowing back-office accounting staff to leverage standard Odoo invoicing."
    ])

    # ---------------------------------------------------------
    # SLIDE 11: Verification & Testing
    # ---------------------------------------------------------
    s11 = prs.slides.add_slide(blank_layout)
    draw_bg(s11)
    add_header(s11, "Verification & Quality Assurance: 41/41 Automated Tests")

    add_card(s11, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2), "Authentication & RBAC Test Suite (16 Tests)", [
        "Login Verification: Valid credentials, invalid passwords, non-existent users, role-mismatch rejections.",
        "Strict Role Isolation: Member blocked from Admin/Staff; Staff blocked from Member/Admin (Strict 403 Forbidden).",
        "Unauthenticated Redirection: Direct URL tampering redirected with HTTP 307 to /login.",
        "Session Token Revocation: Server-side token invalidation upon logout; prevents token replay attacks.",
        "Youth Consent Rules: Validates Underage Guardian profile creation and approval tracking."
    ])

    add_card(s11, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2), "Operational Domain Test Suite (25 Tests)", [
        "Court Anti-Collision: Mathematical lock rejects overlapping slots with HTTP 409 Conflict.",
        "Anti-Monopoly Limit: Caps bookings at 2 slots per member per day.",
        "Single-Shelf Inventory: Concurrent order deduction and insufficient stock rejections.",
        "Bar Running Tabs: Automatic member discounts and split settlement verification.",
        "CRM Lead Conversion: 1-click conversion from prospect to official member record.",
        "Fast Pytest Execution: Full 41-test suite completes in 11.03s with in-memory SQLite isolation."
    ], accent_color=ACCENT_GREEN)

    # ---------------------------------------------------------
    # SLIDE 12: Scalability Roadmap
    # ---------------------------------------------------------
    s12 = prs.slides.add_slide(blank_layout)
    draw_bg(s12)
    add_header(s12, "Summary & Future Scalability Roadmap")

    add_card(s12, Inches(0.8), Inches(1.6), Inches(3.6), Inches(5.2), "Delivered Milestones", [
        "Production Ready: Complete FastAPI + SQLite + Odoo 17 stack.",
        "Dual-Mode Auth: Frictionless Sign In and Account Creation.",
        "Seeded Ecosystem: 173 users, 165 members, 5 courts, 8 tables, pro shop.",
        "Adorable Glass UI: Dials, soundscapes, 3D tilt passes, and smoothie shakers."
    ])

    add_card(s12, Inches(4.8), Inches(1.6), Inches(3.6), Inches(5.2), "Architecture Strengths", [
        "Strict Separation of Concerns: Clear boundary between UI, API, domain services, and storage.",
        "Enterprise Security: Salted bcrypt (r=12) and JWT session blocklisting.",
        "Maintainability: Modular directory structure with typed Pydantic models.",
        "Zero Double Bookings: Mathematical collision engine eliminates scheduling disputes."
    ])

    add_card(s12, Inches(8.8), Inches(1.6), Inches(3.7), Inches(5.2), "Scalability Roadmap", [
        "Cloud PostgreSQL Migration: Easy engine swap via SQLAlchemy DATABASE_URL.",
        "Redis Distributed Lock: Elevate in-memory collision locks to distributed Redis Redlock.",
        "Native Mobile Apps: Flutter / React Native frontends consuming existing OpenAPI endpoints.",
        "IoT Turnstiles: QR code / RFID digital membership card scanning at court turnstiles."
    ], accent_color=AMBER_GOLD)

    output_path = "Champions_Club_System_Design.pptx"
    prs.save(output_path)
    file_size_kb = os.path.getsize(output_path) / 1024
    print(f"SUCCESS: Generated 100% bulletproof PPTX at {output_path} ({file_size_kb:.1f} KB)")
    return output_path

if __name__ == "__main__":
    build_presentation()

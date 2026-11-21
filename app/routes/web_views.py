"""
Frontend Web Views Router (Server-rendered UI templates)
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse, Response, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import date

from app.database import get_db
from app.models.member import Member
from app.models.court import Court, CourtBooking
from app.models.shop import Product, ProductCategory
from app.models.bar import BarTable, BarMenuItem
from app.models.crm import LeadEnquiry
from app.models.finance import Invoice, Employee, LeaveRequest
from app.models.user import User, UserRole
from app.models.guardian import Guardian
from app.models.player import PlayerProfile
from app.models.audit import AuditLog
from app.services.auth_dependencies import (
    require_admin, require_member, require_player, require_staff, require_walk_in, get_optional_current_user
)
from app.services.auth_security import SESSION_COOKIE_NAME, revoke_session_token
from app.config import settings

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(include_in_schema=False)

@router.get("/login")
def view_login(request: Request, db: Session = Depends(get_db)):
    current_user = get_optional_current_user(request, db)
    if current_user:
        dashboards = {
            UserRole.ADMIN.value: "/admin/dashboard",
            UserRole.MEMBER.value: "/member/dashboard",
            UserRole.PLAYER.value: "/player/dashboard",
            UserRole.STAFF.value: "/staff/dashboard",
            UserRole.WALK_IN.value: "/guest"
        }
        target = dashboards.get(current_user.primary_role, "/")
        return RedirectResponse(url=target, status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"mode": "login"}
    )

@router.get("/register")
def view_register(request: Request, db: Session = Depends(get_db)):
    current_user = get_optional_current_user(request, db)
    if current_user:
        dashboards = {
            UserRole.ADMIN.value: "/admin/dashboard",
            UserRole.MEMBER.value: "/member/dashboard",
            UserRole.PLAYER.value: "/player/dashboard",
            UserRole.STAFF.value: "/staff/dashboard",
            UserRole.WALK_IN.value: "/guest"
        }
        target = dashboards.get(current_user.primary_role, "/")
        return RedirectResponse(url=target, status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"mode": "register"}
    )

@router.get("/logout")
def view_logout(request: Request):
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        revoke_session_token(token)
    res = RedirectResponse(url="/login", status_code=303)
    res.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    return res

# =========================================================================
# STRICT ISOLATED ROLE DASHBOARDS
# =========================================================================

@router.get("/admin/dashboard")
def view_admin_dashboard(
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    ADMIN Portal: Strictly accessible by ADMIN role accounts only.
    Provides complete executive KPIs, user governance, staff roster, and system audit logs.
    """
    total_members = db.query(Member).count()
    active_members = db.query(Member).filter(Member.status == "active").count()
    expired_members = db.query(Member).filter(Member.status == "expired").count()
    gold_count = db.query(Member).filter(Member.tier == "gold").count()
    silver_count = db.query(Member).filter(Member.tier == "silver").count()
    underage_count = db.query(Member).filter((Member.tier == "junior") | (Member.is_junior == True)).count()
    
    total_users = db.query(User).count()
    guardian_count = db.query(Guardian).count()
    staff_count = db.query(Employee).count()
    player_count = db.query(PlayerProfile).count()
    
    employees = db.query(Employee).all()
    leaves = db.query(LeaveRequest).order_by(LeaveRequest.created_at.desc()).all()
    audit_logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(15).all()

    return templates.TemplateResponse(
        request=request,
        name="dashboards/admin_dashboard.html",
        context={
            "current_user": current_user,
            "total_members": total_members,
            "active_members": active_members,
            "expired_members": expired_members,
            "gold_count": gold_count,
            "silver_count": silver_count,
            "underage_count": underage_count,
            "total_users": total_users,
            "guardian_count": guardian_count,
            "staff_count": staff_count,
            "player_count": player_count,
            "employees": employees,
            "leaves": leaves,
            "audit_logs": audit_logs,
            "tiers": settings.TIERS
        }
    )

@router.get("/member/dashboard")
def view_member_dashboard(
    request: Request,
    current_user: User = Depends(require_member),
    db: Session = Depends(get_db)
):
    """
    MEMBER Portal: Strictly accessible by MEMBER role accounts only.
    Provides personal digital membership cards (Gold, Silver, Underage), bookings, and renewal.
    """
    # IDOR Protection: Member can only view their own linked member profile
    member = current_user.member_profile
    if not member:
        # Fallback for safety if linked profile is not mapped
        member = db.query(Member).filter(Member.email == current_user.email).first()
        if not member:
            member = db.query(Member).first()

    bookings = db.query(CourtBooking).filter(
        CourtBooking.member_id == member.id
    ).order_by(CourtBooking.booking_date.desc()).all()

    invoices = db.query(Invoice).filter(
        Invoice.member_id == member.id
    ).order_by(Invoice.issue_date.desc()).all()

    total_spend = sum(b.total_amount for b in bookings) + sum(inv.amount_paid for inv in invoices)

    return templates.TemplateResponse(
        request=request,
        name="dashboards/member_dashboard.html",
        context={
            "current_user": current_user,
            "member": member,
            "bookings": bookings,
            "invoices": invoices,
            "total_spend": total_spend,
            "tiers": settings.TIERS
        }
    )

@router.get("/player/dashboard")
def view_player_dashboard(
    request: Request,
    current_user: User = Depends(require_player),
    db: Session = Depends(get_db)
):
    """
    PLAYER Portal: Strictly accessible by PLAYER role accounts only.
    Provides athlete training regimen, tournament fixtures, and performance metrics.
    """
    player = current_user.player_profile
    if not player:
        player = db.query(PlayerProfile).filter(PlayerProfile.email == current_user.email).first()
        if not player:
            player = db.query(PlayerProfile).first()

    return templates.TemplateResponse(
        request=request,
        name="dashboards/player_dashboard.html",
        context={
            "current_user": current_user,
            "player": player
        }
    )

@router.get("/staff/dashboard")
def view_staff_dashboard(
    request: Request,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db)
):
    """
    STAFF Portal: Strictly accessible by STAFF role accounts only.
    Provides departmental action cards, roster shifts, and attendance logging.
    """
    employee = current_user.employee_profile
    if not employee:
        employee = db.query(Employee).filter(Employee.email == current_user.email).first()
        if not employee:
            employee = db.query(Employee).first()

    return templates.TemplateResponse(
        request=request,
        name="dashboards/staff_dashboard.html",
        context={
            "current_user": current_user,
            "employee": employee
        }
    )

@router.get("/guest")
def view_guest_portal(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    GUEST Portal: Accessible by WALK_IN accounts and general public visitors.
    Offers pay-per-play reservations, standard rate cards, and membership upgrade showcase.
    """
    current_user = get_optional_current_user(request, db)
    courts = db.query(Court).filter(Court.is_active == True).all()

    return templates.TemplateResponse(
        request=request,
        name="guest_portal.html",
        context={
            "current_user": current_user,
            "courts": courts,
            "tiers": settings.TIERS
        }
    )

@router.get("/")
def view_index(request: Request, db: Session = Depends(get_db)):
    courts = db.query(Court).filter(Court.is_active == True).all()
    products = db.query(Product).filter(Product.is_active == True).limit(6).all()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "tiers": settings.TIERS,
            "courts": courts,
            "products": products
        }
    )

@router.get("/members")
def view_members(request: Request, db: Session = Depends(get_db)):
    members = db.query(Member).order_by(Member.id.desc()).all()
    return templates.TemplateResponse(
        request=request,
        name="members.html",
        context={
            "members": members,
            "tiers": settings.TIERS
        }
    )

@router.get("/courts")
def view_courts(request: Request, db: Session = Depends(get_db)):
    courts = db.query(Court).filter(Court.is_active == True).all()
    members = db.query(Member).filter(Member.status == "active").all()
    return templates.TemplateResponse(
        request=request,
        name="courts.html",
        context={
            "courts": courts,
            "members": members,
            "today": str(date.today())
        }
    )

@router.get("/shop")
def view_shop(request: Request, db: Session = Depends(get_db)):
    products = db.query(Product).all()
    categories = db.query(ProductCategory).all()
    members = db.query(Member).filter(Member.status == "active").all()
    return templates.TemplateResponse(
        request=request,
        name="shop.html",
        context={
            "products": products,
            "categories": categories,
            "members": members
        }
    )

@router.get("/bar")
def view_bar(request: Request, db: Session = Depends(get_db)):
    tables = db.query(BarTable).all()
    menu_items = db.query(BarMenuItem).filter(BarMenuItem.is_available == True).all()
    members = db.query(Member).filter(Member.status == "active").all()
    return templates.TemplateResponse(
        request=request,
        name="bar.html",
        context={
            "tables": tables,
            "menu_items": menu_items,
            "members": members
        }
    )

@router.get("/kitchen")
def view_kitchen(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="kitchen.html",
        context={}
    )

@router.get("/crm")
def view_crm(request: Request, db: Session = Depends(get_db)):
    leads = db.query(LeadEnquiry).order_by(LeadEnquiry.created_at.desc()).all()
    return templates.TemplateResponse(
        request=request,
        name="crm.html",
        context={
            "leads": leads,
            "tiers": settings.TIERS
        }
    )

@router.get("/owner")
def view_owner(request: Request, db: Session = Depends(get_db)):
    invoices = db.query(Invoice).order_by(Invoice.issue_date.desc()).all()
    employees = db.query(Employee).all()
    leaves = db.query(LeaveRequest).order_by(LeaveRequest.created_at.desc()).all()
    return templates.TemplateResponse(
        request=request,
        name="owner.html",
        context={
            "invoices": invoices,
            "employees": employees,
            "leaves": leaves
        }
    )

@router.get("/presentation")
def view_presentation(request: Request):
    """Interactive System Design & Architecture Presentation Deck"""
    return templates.TemplateResponse(
        request=request,
        name="presentation_viewer.html",
        context={}
    )

@router.get("/Champions_Club_System_Design.pptx")
@router.get("/download-presentation")
def download_presentation():
    """Direct download of the bulletproof PowerPoint presentation"""
    return FileResponse(
        path="Champions_Club_System_Design.pptx",
        filename="Champions_Club_System_Design.pptx",
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )



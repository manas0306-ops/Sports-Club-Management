"""
Frontend Web Views Router (Server-rendered UI templates)
"""
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import date

from app.database import get_db
from app.models.member import Member
from app.models.court import Court
from app.models.shop import Product, ProductCategory
from app.models.bar import BarTable, BarMenuItem
from app.models.crm import LeadEnquiry
from app.models.finance import Invoice, Employee, LeaveRequest
from app.config import settings

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(include_in_schema=False)

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

"""
The Champions Club Management System - Main FastAPI Application
"""
import os
from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
import app.models # registers models
from app.routes import api_members, api_courts, api_shop, api_bar, api_crm, api_finance, web_views

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Unified Digital Backbone for The Champions Club (Odoo Hackathon Challenge)",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include API Routers
app.include_router(api_members.router, prefix=settings.API_V1_STR)
app.include_router(api_courts.router, prefix=settings.API_V1_STR)
app.include_router(api_shop.router, prefix=settings.API_V1_STR)
app.include_router(api_bar.router, prefix=settings.API_V1_STR)
app.include_router(api_crm.router, prefix=settings.API_V1_STR)
app.include_router(api_finance.router, prefix=settings.API_V1_STR)

# Include Web View Routers
app.include_router(web_views.router)

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

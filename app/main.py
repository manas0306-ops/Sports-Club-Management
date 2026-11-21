"""
The Champions Club Management System - Main FastAPI Application
"""
import os
from fastapi import FastAPI, Response, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
import app.models # registers models
from app.routes import api_auth, api_members, api_courts, api_shop, api_bar, api_crm, api_finance, web_views

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
app.include_router(api_auth.router, prefix=settings.API_V1_STR)
app.include_router(api_members.router, prefix=settings.API_V1_STR)
app.include_router(api_courts.router, prefix=settings.API_V1_STR)
app.include_router(api_shop.router, prefix=settings.API_V1_STR)
app.include_router(api_bar.router, prefix=settings.API_V1_STR)
app.include_router(api_crm.router, prefix=settings.API_V1_STR)
app.include_router(api_finance.router, prefix=settings.API_V1_STR)

# Include Web View Routers
app.include_router(web_views.router)

from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

html_templates = Jinja2Templates(directory="app/templates")

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 307:
        return Response(status_code=307, headers=exc.headers)
    
    accept = request.headers.get("accept", "")
    if "text/html" in accept and not request.url.path.startswith("/api/"):
        if exc.status_code == 403:
            from app.services.auth_dependencies import get_optional_current_user
            from app.database import SessionLocal
            db = SessionLocal()
            try:
                user = get_optional_current_user(request, db)
            finally:
                db.close()
            return html_templates.TemplateResponse(
                request=request,
                name="errors/403.html",
                context={"detail": exc.detail, "current_user": user},
                status_code=403
            )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

"""
FastAPI application for SCLAPP — Lead Generation & Scraping platform.
Serves the API under /api and the frontend (SPA) at /.
"""

from pathlib import Path
import mimetypes

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.core.config import get_settings
from backend.api.v1 import auth, companies, dashboard, scraping, emails, profile

# Ensure correct MIME types for static assets
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("application/javascript", ".mjs")
mimetypes.add_type("text/css", ".css")

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
FRONTEND_ASSETS = FRONTEND_DIR / "assets"
INDEX_FILE = FRONTEND_DIR / "index.html"

app = FastAPI(
    title="SCLAPP API",
    description="Lead Generation & Scraping platform for tech startups in Colombia",
    version="1.0.0",
)

# CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings["cors_origins"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers
app.include_router(auth.router, prefix="/api")
app.include_router(companies.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(scraping.router, prefix="/api")
app.include_router(emails.router, prefix="/api")
app.include_router(profile.router, prefix="/api")


@app.get("/health")
def health():
    """Health check for Render / monitoring."""
    return {"status": "ok"}


# Serve static frontend assets
if FRONTEND_ASSETS.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_ASSETS)), name="assets")


@app.get("/")
def serve_spa_root():
    """Serve SPA entrypoint at root."""
    if INDEX_FILE.exists():
        return FileResponse(str(INDEX_FILE))
    return {"message": "SCLAPP API is running", "docs": "/docs"}


@app.get("/{full_path:path}")
def serve_spa_fallback(full_path: str):
    """
    Serve index.html for SPA routes such as /dashboard or /companies.
    Excludes API and docs routes.
    """
    blocked_prefixes = ("api/", "docs", "openapi", "redoc", "health", "assets/")
    if full_path.startswith(blocked_prefixes):
        raise HTTPException(status_code=404, detail="Not Found")

    if INDEX_FILE.exists():
        return FileResponse(str(INDEX_FILE))

    raise HTTPException(status_code=404, detail="Frontend not found")
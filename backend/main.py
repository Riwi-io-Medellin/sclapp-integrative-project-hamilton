"""
FastAPI application for SCLAPP — Lead Generation & Scraping platform.
Serves the API under /api and the frontend (SPA) at /.
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.core.config import get_settings
from backend.api.v1 import auth, companies, dashboard, scraping, emails, profile

# Path to frontend (project root / frontend)
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
FRONTEND_ASSETS = FRONTEND_DIR / "assets"

app = FastAPI(
    title="SCLAPP API",
    description="Lead Generation & Scraping platform for tech startups in Colombia",
    version="1.0.0",
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings["cors_origins"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers first (under /api)
app.include_router(auth.router, prefix="/api")
app.include_router(companies.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(scraping.router, prefix="/api")
app.include_router(emails.router, prefix="/api")
app.include_router(profile.router, prefix="/api")


@app.get("/health")
def health():
    """Health check for load balancers or monitoring."""
    return {"status": "ok"}


# Static assets (CSS, JS, images)
if FRONTEND_ASSETS.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_ASSETS)), name="assets")


# SPA: serve index.html for / and for any non-API path so the frontend router can handle hash routes
@app.get("/")
def serve_spa_root():
    """Serve the single-page app entry (index.html) at root."""
    if not FRONTEND_DIR.exists():
        return {"message": "SCLAPP API is running", "docs": "/docs"}
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        return {"message": "SCLAPP API is running", "docs": "/docs"}
    return FileResponse(str(index_path))


@app.get("/{full_path:path}")
def serve_spa_fallback(full_path: str):
    """Return index.html for SPA routes (so refresh on /dashboard etc. works)."""
    if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("openapi"):
        raise HTTPException(status_code=404, detail="Not Found")
    if not (FRONTEND_DIR / "index.html").exists():
        raise HTTPException(status_code=404, detail="Not Found")
    return FileResponse(str(FRONTEND_DIR / "index.html"))

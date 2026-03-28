"""
NormClaim — Main FastAPI Application
AI-powered Clinical & Administrative Data Normalization Engine
for Indian SME hospitals.

Run with: uvicorn main:app --reload --port 8000
"""

import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from supabase import create_client, Client
from services.persistence_service import verify_supabase_database

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

# ── Configure logging ─────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("normclaim")

# ── Create FastAPI app ────────────────────────────────────────────────────
app = FastAPI(
    title="NormClaim API",
    description=(
        "AI-powered Clinical & Administrative Data Normalization Engine. "
        "Upload discharge summaries, extract clinical entities via Gemini AI, "
        "generate FHIR R4 bundles, and run ICD-10 claim reconciliation."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS middleware ───────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Include routers ──────────────────────────────────────────────────────
from routers.documents import router as documents_router
from routers.extract import router as extract_router
from routers.fhir import router as fhir_router
from routers.reconcile import router as reconcile_router
from routers.review import router as review_router
from routers.feedback import router as feedback_router
from routers.validate import router as validate_router
from routers.analytics import router as analytics_router

app.include_router(documents_router)
app.include_router(extract_router)
app.include_router(fhir_router)
app.include_router(reconcile_router)
app.include_router(review_router)
app.include_router(feedback_router)
app.include_router(analytics_router)
app.include_router(validate_router)


# ── Supabase Client Setup ────────────────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY")

supabase: Optional[Client] = None
supabase_db_status = {
    "connected": False,
    "missing_tables": [],
    "ok": False,
}
if not SUPABASE_URL or not SUPABASE_KEY:
    logger.warning("Supabase credentials not set. Running with in-memory fallback for uploads/listing.")
else:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("✓  Supabase client initialized successfully")
    try:
        supabase_db_status = verify_supabase_database(supabase)
        if supabase_db_status["ok"]:
            logger.info("✓  Supabase database connectivity verified and required tables are present")
        else:
            missing = ", ".join(supabase_db_status.get("missing_tables", [])) or "unknown"
            logger.warning("⚠  Supabase connected but missing required tables: %s", missing)
    except Exception as e:
        logger.warning("⚠  Supabase verification failed: %s", e)

# ── Health check ──────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health():
    """Health check endpoint."""
    gemini_configured = bool(os.environ.get("GEMINI_API_KEY"))
    supabase_configured = bool(SUPABASE_URL and SUPABASE_KEY)
    return {
        "status": "ok",
        "service": "normclaim-backend",
        "version": "1.0.0",
        "gemini_api_key_configured": gemini_configured,
        "supabase_configured": supabase_configured,
        "supabase_connected": bool(supabase_db_status.get("connected")),
        "supabase_db_ready": bool(supabase_db_status.get("ok")),
        "supabase_missing_tables": supabase_db_status.get("missing_tables", []),
    }


# ── Startup event ────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("  NormClaim Backend — Starting up")
    logger.info("=" * 60)

    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if not gemini_key or gemini_key == "your_gemini_api_key_here":
        logger.warning(
            "⚠  GEMINI_API_KEY not set! "
            "Get one free at: https://aistudio.google.com/app/apikey"
        )
    else:
        logger.info(f"✓  Gemini API key configured (ends with ...{gemini_key[-4:]})")

    fhir_url = os.environ.get("FHIR_SERVICE_URL", "http://localhost:8001/fhir/bundle")
    logger.info(f"✓  FHIR service URL: {fhir_url}")
    if supabase is not None and not supabase_db_status.get("ok"):
        logger.warning("⚠  Supabase database is not fully ready. Check missing tables in /health response.")
    logger.info("✓  API docs available at: http://localhost:8000/docs")
    logger.info("=" * 60)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

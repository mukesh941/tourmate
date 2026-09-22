"""
FastAPI app entrypoint. Route handlers stay thin (see app/api/routes/*);
business logic lives in app/services/*.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# ... existing imports ...
from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.api.routes.destinations import router as destinations_router
from app.api.routes.categories import router as categories_router
from app.api.routes.places import router as places_router
from app.api.routes.ai import router as ai_router
from app.api.routes.itineraries import router as itineraries_router
from app.api.routes.interactions import router as interactions_router
from app.api.routes.admin import router as admin_router
from app.api.routes.guides import router as guides_router
from app.api.routes.applications import router as applications_router
from app.api.routes.hotels import router as hotels_router
from app.api.routes.restaurants import router as restaurants_router
from app.api.routes.activities import router as activities_router
from app.api.routes.locations import router as locations_router
from app.api.routes.google_places import router as google_places_router
from app.core.config import settings
from app.core.database import ensure_indexes
from app.core.limiter import limiter

import asyncio
from app.core.db import async_engine, AsyncSessionLocal
from app.core.database import close_client

async def _run_startup_tasks_safely():
    # 1. Alembic migrations (verified non-blockingly)
    try:
        import os
        from alembic.config import Config
        from alembic import command
        ini_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "alembic.ini")
        if os.path.exists(ini_path):
            alembic_cfg = Config(ini_path)
            await asyncio.wait_for(asyncio.to_thread(command.upgrade, alembic_cfg, "head"), timeout=15.0)
            logging.info("Alembic migrations verified successfully.")
    except Exception as exc:
        logging.warning("Alembic auto-migration check skipped or timed out: %s", exc)

    # 2. Legacy Mongo index check (only if non-localhost and configured)
    try:
        if settings.mongo_uri and ("localhost" not in settings.mongo_uri or settings.environment == "development"):
            await asyncio.wait_for(ensure_indexes(), timeout=5.0)
    except Exception as exc:
        logging.warning("MongoDB index check skipped: %s", exc)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Launch background tasks without delaying port binding
    bg_task = asyncio.create_task(_run_startup_tasks_safely())
    yield
    # Shutdown: Cleanly dispose resources
    try:
        if not bg_task.done():
            bg_task.cancel()
    except Exception:
        pass
    try:
        await async_engine.dispose()
        logging.info("Async database engine disposed successfully.")
    except Exception as exc:
        logging.warning("Error disposing database engine: %s", exc)
    try:
        close_client()
        logging.info("MongoDB client closed successfully.")
    except Exception as exc:
        logging.warning("Error closing MongoDB client: %s", exc)

app = FastAPI(title="TourMate AI API", version="0.1.0", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logging.exception("Unhandled server exception on %s %s: %s", request.method, request.url.path, exc)
    is_dev = settings.environment.lower() in ("development", "dev", "test")
    err_detail = str(exc) if is_dev else "An unexpected internal server error occurred."
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "error": {"message": "Internal server error", "detail": err_detail},
        },
    )


app.add_middleware(SlowAPIMiddleware)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    try:
        response: Response = await call_next(request)
    except Exception as exc:
        logging.exception("Unhandled error processing %s %s: %s", request.method, request.url.path, exc)
        is_dev = settings.environment.lower() in ("development", "dev", "test")
        err_detail = str(exc) if is_dev else "An unexpected internal server error occurred."
        response = JSONResponse(
            status_code=500,
            content={
                "success": False,
                "data": None,
                "error": {"message": "Internal server error", "detail": err_detail},
            },
        )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=r"^https://[\w-]+\.vercel\.app$|^https://[\w-]+\.netlify\.app$|^http://localhost(:\d+)?$|^http://127\.0\.0\.1(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(destinations_router, prefix="/api")
app.include_router(categories_router, prefix="/api")
app.include_router(places_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
app.include_router(itineraries_router, prefix="/api")
app.include_router(interactions_router, prefix="/api/interactions")
app.include_router(interactions_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(guides_router, prefix="/api")
app.include_router(applications_router, prefix="/api")
app.include_router(hotels_router, prefix="/api")
app.include_router(restaurants_router, prefix="/api")
app.include_router(activities_router, prefix="/api")
app.include_router(locations_router, prefix="/api")
app.include_router(google_places_router, prefix="/api")

@app.get("/")
async def root():
    return {"success": True, "data": {"message": "TourMate AI API"}, "error": None}

@app.get("/health")
@app.get("/api/health")
async def health():
    """
    Lightweight, ultra-fast liveness check.
    Zero external calls, zero database queries, zero AI/model loading.
    Must respond < 5ms for container health checkers (Render, Kubernetes).
    """
    return {"success": True, "data": {"status": "ok"}, "error": None}


@app.get("/ready")
@app.get("/api/ready")
async def ready():
    """
    Readiness probe verifying core dependencies (PostgreSQL database connectivity).
    Uses a strict 2-second timeout so it never hangs.
    """
    db_status = "unknown"
    try:
        from sqlalchemy import text
        # Verify database connectivity with strict 2-second timeout
        async with asyncio.timeout(2.0):
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
                db_status = "connected"
    except Exception as exc:
        logging.warning("Readiness probe database check failed: %s", exc)
        db_status = "disconnected"
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "data": {"status": "unready", "database": db_status},
                "error": {"message": "Service unavailable: database connection check failed"},
            },
        )

    return {
        "success": True,
        "data": {"status": "ready", "database": db_status},
        "error": None,
    }

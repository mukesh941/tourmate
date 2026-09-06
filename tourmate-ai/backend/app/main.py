"""
FastAPI app entrypoint. Route handlers stay thin (see app/api/routes/*);
business logic lives in app/services/*.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
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
from app.core.config import settings
from app.core.database import ensure_indexes
from app.core.limiter import limiter

@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_indexes()
    yield

app = FastAPI(title="TourMate AI API", version="0.1.0", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
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
app.include_router(admin_router, prefix="/api")
app.include_router(guides_router, prefix="/api")



@app.get("/api/health")
async def health():
    return {"success": True, "data": {"status": "ok"}, "error": None}

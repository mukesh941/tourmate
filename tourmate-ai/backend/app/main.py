"""
FastAPI app entrypoint. Route handlers stay thin (see app/api/routes/*);
business logic lives in app/services/*.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.api.routes.destinations import router as destinations_router
from app.api.routes.categories import router as categories_router
from app.api.routes.places import router as places_router
from app.api.routes.ai import router as ai_router
from app.api.routes.itineraries import router as itineraries_router
from app.api.routes.interactions import router as interactions_router
from app.api.routes.admin import router as admin_router
from app.core.config import settings
from app.core.database import ensure_indexes


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_indexes()
    yield


app = FastAPI(title="TourMate AI API", version="0.1.0", lifespan=lifespan)

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



@app.get("/api/health")
async def health():
    return {"success": True, "data": {"status": "ok"}, "error": None}

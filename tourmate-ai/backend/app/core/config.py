"""
Central app configuration, loaded from environment variables.
Nothing here is a secret literal - all values come from .env (see .env.example).
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # PostgreSQL + pgvector
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5435/tourmate"

    # Backward-compatible MongoDB configuration (optional during transition)
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "tourmate"

    # JWT Authentication
    jwt_secret_key: str = "tourmate-super-secret-production-key-replace-in-env"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7

    # Networking & CORS
    environment: str = "development"
    cors_origins: str = "https://frontend-delta-six-hf0z79dpo8.vercel.app,http://localhost:5173,http://127.0.0.1:5173,https://tourmate-ai.netlify.app,https://tourmate.vercel.app,http://localhost:3000"
    gemini_api_key: str | None = None
    google_maps_api_key: str | None = None

    # Phase 4 Routing & Optimization Configuration
    routing_v_max_kmh: float = 100.0
    max_daily_candidate_pois: int = 8

    # Phase 5 RAG & AI Assistant Configuration
    gemini_model: str = "gemini-3.6-flash"
    rag_top_k: int = 4
    rag_min_similarity: float = 0.40

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        if "http://localhost:5173" in origins and "http://127.0.0.1:5173" not in origins:
            origins.append("http://127.0.0.1:5173")
        if "https://frontend-delta-six-hf0z79dpo8.vercel.app" not in origins:
            origins.append("https://frontend-delta-six-hf0z79dpo8.vercel.app")
        return origins if origins else ["https://frontend-delta-six-hf0z79dpo8.vercel.app", "http://localhost:5173", "http://127.0.0.1:5173"]

    @property
    def async_database_url(self) -> str:
        """Returns asynchronous connection URL normalized for asyncpg."""
        url = self.database_url
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @property
    def sync_database_url(self) -> str:
        """Returns standard psycopg2 synchronous connection URL for migrations & tools."""
        url = self.database_url
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+psycopg2://", 1)
        if url.startswith("postgresql+asyncpg://"):
            return url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return url


settings = Settings()

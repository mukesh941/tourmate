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
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,https://tourmate-ai.netlify.app,https://tourmate.vercel.app,http://localhost:3000"
    gemini_api_key: str | None = None
    google_maps_api_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        if "http://localhost:5173" in origins and "http://127.0.0.1:5173" not in origins:
            origins.append("http://127.0.0.1:5173")
        return origins if origins else ["http://localhost:5173", "http://127.0.0.1:5173"]

    @property
    def sync_database_url(self) -> str:
        """Returns standard psycopg2 synchronous connection URL for migrations & tools."""
        url = self.database_url
        if url.startswith("postgresql+asyncpg://"):
            return url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return url


settings = Settings()

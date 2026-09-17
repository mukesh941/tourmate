"""
Central app configuration, loaded from environment variables.
Nothing here is a secret literal - all values come from .env (see .env.example).
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "tourmate"

    jwt_secret_key: str = "tourmate-super-secret-production-key-replace-in-env"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7

    cors_origins: str = "http://localhost:5173,https://tourmate-ai.netlify.app,https://tourmate.vercel.app,http://localhost:3000"
    gemini_api_key: str | None = None
    google_maps_api_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        return origins if origins else ["http://localhost:5173"]


settings = Settings()


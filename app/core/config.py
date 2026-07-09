"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings, populated from `.env` / environment."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- General ---
    PROJECT_NAME: str = "E-commerce Backend API"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # --- Database ---
    DATABASE_URL: str
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # --- Redis ---
    # Set USE_REDIS=true once a real Redis instance is available. Until then the app
    # falls back to an in-process in-memory cache (app/core/redis.py) — same interface,
    # zero external dependency, but state is per-process and lost on restart.
    USE_REDIS: bool = False
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_SECONDS: int = 300

    # --- JWT ---
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- Supabase Storage ---
    # SUPABASE_URL: str
    # SUPABASE_SERVICE_ROLE_KEY: str
    # SUPABASE_STORAGE_BUCKET: str
    
    SUPABASE_S3_ENDPOINT_URL: str
    SUPABASE_S3_ACCESS_KEY_ID: str
    SUPABASE_S3_SECRET_ACCESS_KEY: str
    SUPABASE_S3_REGION: str
    SUPABASE_S3_BUCKET_NAME: str
    SUPABASE_PROJECT_URL: str

    # --- CORS ---
    # Comma-separated list of allowed origins, e.g. "http://localhost:4200,http://localhost:4500".
    # Defaults cover Angular's standard dev port plus the alternate port used during local testing.
    FRONTEND_URL: str = "http://localhost:4200,http://localhost:4500"

    # --- File upload ---
    MAX_UPLOAD_SIZE_MB: int = 5
    ALLOWED_IMAGE_CONTENT_TYPES: tuple[str, ...] = (
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
    )
    MAX_VIDEO_UPLOAD_SIZE_MB: int = 50
    ALLOWED_VIDEO_CONTENT_TYPES: tuple[str, ...] = (
        "video/mp4",
        "video/webm",
        "video/quicktime",
    )

    # --- Rate limiting ---
    RATE_LIMIT_PER_MINUTE: int = 60

    @property
    def MAX_UPLOAD_SIZE_BYTES(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def MAX_VIDEO_UPLOAD_SIZE_BYTES(self) -> int:
        return self.MAX_VIDEO_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.FRONTEND_URL.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached `Settings` instance (singleton for process lifetime)."""
    return Settings()


settings = get_settings()

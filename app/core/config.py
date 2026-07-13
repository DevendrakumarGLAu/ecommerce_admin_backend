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
    # FRONTEND_URL: str = "http://localhost:4200,http://localhost:4500"
    FRONTEND_URL:str = "https://banglesbazaar.onrender.com"

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

    # --- Login captcha ---
    CAPTCHA_EXPIRY_MINUTES: int = 5
    CAPTCHA_LENGTH: int = 6

    # --- Forgot-password OTP ---
    OTP_EXPIRY_MINUTES: int = 5
    OTP_RESET_TOKEN_EXPIRY_MINUTES: int = 10
    OTP_MAX_ATTEMPTS: int = 5
    # True echoes the OTP back in the /auth/forgot-password response, independent of
    # whether SMTP is configured — handy while testing, but turn this off in production
    # so the OTP is only ever delivered by email. Defaults to False now that Gmail SMTP
    # delivery (below) is the real path; flip to True if you need to test without a
    # working Gmail App Password on hand.
    OTP_DEBUG_MODE: bool = False

    # --- Email delivery (Gmail SMTP via App Password — no paid/third-party API) ---
    # Swappable: this whole flow only touches app/services/email/*. To move off Gmail
    # later, add a new EmailProvider implementation and change get_email_provider() in
    # app/services/email/__init__.py — nothing in otp_notifier.py or the password-reset
    # service needs to change.
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""  # your Gmail address
    SMTP_APP_PASSWORD: str = ""  # Gmail App Password — NOT your normal account password
    SMTP_FROM_EMAIL: str = ""  # defaults to SMTP_USERNAME when blank
    SMTP_FROM_NAME: str = "Firozabad Bangles"

    @property
    def smtp_configured(self) -> bool:
        return bool(self.SMTP_USERNAME and self.SMTP_APP_PASSWORD)

    @property
    def smtp_from_address(self) -> str:
        return self.SMTP_FROM_EMAIL or self.SMTP_USERNAME

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

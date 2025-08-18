from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    APP_NAME: str = Field(default="Holover App")
    ENV: str = Field(default="development")
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    LOG_LEVEL: str = Field(default="INFO")
    CORS_ORIGINS: str = Field(default="http://localhost:3000,http://localhost:8000")

    SECRET_KEY: str = Field(default="change-me")
    ENCRYPTION_KEY: str = Field(default="change-me-32-bytes")

    DATABASE_URL: str = Field(default="postgresql+psycopg://postgres:postgres@localhost:5432/holover")

    TIKTOK_CLIENT_KEY: str = Field(default="")
    TIKTOK_CLIENT_SECRET: str = Field(default="")
    TIKTOK_REDIRECT_URI: str = Field(default="http://localhost:8000/auth/callback")
    TIKTOK_SCOPES: str = Field(default="user.info.basic,user.info.profile,user.info.stats,video.upload,video.publish")
    TIKTOK_BASE_URL: str = Field(default="https://open.tiktokapis.com/v2")
    # Authorization endpoint base (separate host from API base)
    TIKTOK_AUTH_BASE_URL: str = Field(default="https://www.tiktok.com/v2/auth/authorize/")

    RATE_LIMIT_MAX_RETRIES: int = Field(default=5)
    RATE_LIMIT_BASE_DELAY_MS: int = Field(default=200)
    RATE_LIMIT_MAX_DELAY_MS: int = Field(default=5000)
    HTTP_TIMEOUT_SECONDS: int = Field(default=30)

    # Content upload (Pull-by-URL) whitelist (comma-separated URL prefixes)
    CONTENT_ALLOWED_URL_PREFIXES: str = Field(default="")

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
    }

settings = Settings()

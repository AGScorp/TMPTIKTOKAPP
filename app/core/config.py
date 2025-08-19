from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
import os

# Load environment variables from .env at import time (explicit python-dotenv)
# This ensures all modules (not only Pydantic) see the vars via os.environ
load_dotenv(dotenv_path=".env", override=False)

class Settings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8100

    TIKTOK_CLIENT_KEY: str = "sbawvu604r2qvzcmkn"
    TIKTOK_CLIENT_SECRET: str = "6J0rKlTMHi85bUx4nBZSz7EJ0fs40ehv"
    TIKTOK_REDIRECT_URI: str = "https://ai-car-damage.agilesoftgroup.com/auth/callback"
    TIKTOK_SCOPES: str = "user.info.basic,user.info.profile,user.info.stats,video.upload,video.publish"
    TIKTOK_BASE_URL: str = "https://open.tiktokapis.com/v2"
    TIKTOK_AUTH_BASE_URL: str = "https://www.tiktok.com"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

    @property
    def scopes_list(self):
        return [s.strip() for s in (self.TIKTOK_SCOPES or "").split(",") if s.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()


import httpx
from app.core.config import settings

def get_http_client() -> httpx.Client:
    return httpx.Client(timeout=settings.HTTP_TIMEOUT_SECONDS)

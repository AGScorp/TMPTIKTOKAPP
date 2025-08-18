from fastapi import APIRouter, Header, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional

from app.integrations.tiktok_client import TikTokClient, TikTokAPIError
from app.core.config import settings

router = APIRouter()
client = TikTokClient()

def _extract_bearer(auth_header: Optional[str]) -> Optional[str]:
    if not auth_header:
        return None
    parts = auth_header.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None

@router.get("/profile")
async def profile(authorization: Optional[str] = Header(None), token: Optional[str] = Query(None)):
    """
    Return TikTok user profile/stats using provided bearer token.
    For local dev without real credentials, client returns a stub response.
    The token is taken from Authorization: Bearer <token> header, or ?token= in query as a fallback.
    """
    access_token = _extract_bearer(authorization) or token
    if not access_token:
        raise HTTPException(status_code=400, detail="missing_access_token")

    try:
        data = await client.get_user_info(access_token)
    except TikTokAPIError as e:
        raise HTTPException(status_code=502, detail=f"tiktok_api_error:{e}") from e
    except Exception:
        raise HTTPException(status_code=500, detail="fetch_user_info_failed")

    return JSONResponse(data)

@router.get("/debug")
def debug(token: Optional[str] = Query(None)):
    """
    Diagnostic endpoint (dev only): shows current ENV, whether client is in dev-mode,
    and whether provided token triggers stub branch.
    """
    # best effort call to the client's dev-mode detector
    try:
        is_dev_mode = client._is_dev_mode()  # type: ignore[attr-defined]
    except Exception:
        is_dev_mode = None
    token_prefix = (token or "")[:8]
    return {
        "env": settings.ENV,
        "client_key_set": bool(settings.TIKTOK_CLIENT_KEY),
        "client_secret_set": bool(settings.TIKTOK_CLIENT_SECRET),
        "is_dev_mode": is_dev_mode,
        "token_startswith_dev": (token or "").startswith("dev_"),
        "token_prefix": token_prefix,
    }

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse

from app.services.oauth import OAuthService
from app.integrations.tiktok_client import TikTokClient, TikTokAPIError
from app.services.tokens import TokenService
from app.core.config import settings

router = APIRouter()
tokens = TokenService()

STATE_COOKIE = "tt_state"

@router.get("/login")
def login():
    """
    Redirect to TikTok consent screen with a secure state cookie.
    """
    oauth = OAuthService()
    state = oauth.generate_state()
    authorize_url = oauth.build_auth_url(state)
    resp = RedirectResponse(authorize_url, status_code=302)
    # In production: set secure=True and domain as appropriate
    resp.set_cookie(
        key=STATE_COOKIE,
        value=state,
        max_age=600,
        httponly=True,
        samesite="lax",
    )
    return resp

@router.get("/callback")
async def callback(request: Request, code: str | None = None, state: str | None = None, error: str | None = None):
    """
    OAuth callback endpoint.
    - Validates state against cookie.
    - Exchanges code -> tokens (dev stub if client creds not set).
    - Fetches user info and persists encrypted tokens (best-effort if DB available).
    """
    if error:
        raise HTTPException(status_code=400, detail=f"oauth_error:{error}")
    oauth = OAuthService()
    cookie_state = request.cookies.get(STATE_COOKIE)
    if not state or not cookie_state or cookie_state != state or not oauth.validate_state(state):
        raise HTTPException(status_code=400, detail="invalid_state")
    if not code:
        raise HTTPException(status_code=400, detail="missing_code")

    client = TikTokClient()
    try:
        token_payload = await client.exchange_code_for_tokens(code)
        access_token = token_payload.get("access_token", "")
        user_info = await client.get_user_info(access_token) if access_token else {"data": {"user": {}}}
    except TikTokAPIError as e:
        raise HTTPException(status_code=502, detail=f"tiktok_api_error:{e}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail="token_exchange_failed") from e

    # Persist tokens (encrypted) and basic profile; tolerate DB not ready
    persisted, user_id, persist_error = tokens.save_user_tokens(user_info, token_payload)

    return JSONResponse({
        "message": "token_obtained",
        "persisted": persisted,
        "user_id": user_id,
        "persist_error": persist_error,
        "user_info": user_info,
        "token": {"token_type": token_payload.get("token_type"), "expires_in": token_payload.get("expires_in"), "scope": token_payload.get("scope")},
    })

@router.post("/refresh")
async def refresh(refresh_token: str | None = None):
    """
    Refresh access token using a provided refresh_token.
    Dev-mode returns stubbed tokens.
    """
    if not refresh_token:
        raise HTTPException(status_code=400, detail="missing_refresh_token")
    client = TikTokClient()
    try:
        data = await client.refresh_token(refresh_token)
    except TikTokAPIError as e:
        raise HTTPException(status_code=502, detail=f"tiktok_api_error:{e}") from e
    except Exception:
        raise HTTPException(status_code=500, detail="refresh_failed")
    return JSONResponse({"message": "token_refreshed", "token": data})

@router.post("/revoke")
async def revoke(access_token: str | None = None):
    """
    Revoke the provided access_token.
    Dev-mode returns stubbed success.
    """
    if not access_token:
        raise HTTPException(status_code=400, detail="missing_access_token")
    client = TikTokClient()
    try:
        data = await client.revoke_token(access_token)
    except TikTokAPIError as e:
        raise HTTPException(status_code=502, detail=f"tiktok_api_error:{e}") from e
    except Exception:
        raise HTTPException(status_code=500, detail="revoke_failed")
    return JSONResponse({"message": "token_revoked", "result": data})

@router.post("/client-token")
async def client_token():
    """
    Obtain an app-level client access token (client_credentials).
    Dev-mode returns a stubbed token.
    """
    client = TikTokClient()
    try:
        data = await client.get_client_access_token()
    except TikTokAPIError as e:
        raise HTTPException(status_code=502, detail=f"tiktok_api_error:{e}") from e
    except Exception:
        raise HTTPException(status_code=500, detail="client_token_failed")
    return JSONResponse({"message": "client_token_obtained", "token": data})

@router.get("/debug")
def auth_debug():
    """
    Diagnostic endpoint to verify OAuth settings loaded by the running process.
    """
    return {
        "client_key": settings.TIKTOK_CLIENT_KEY,
        "redirect_uri": settings.TIKTOK_REDIRECT_URI,
        "scopes": settings.TIKTOK_SCOPES,
        "auth_base": settings.TIKTOK_AUTH_BASE_URL,
        "env": settings.ENV,
    }

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from urllib.parse import urlparse
import logging

from app.services.oauth import OAuthService
from app.integrations.tiktok_client import TikTokClient, TikTokAPIError
from app.services.tokens import TokenService
from app.core.config import settings

router = APIRouter()
tokens = TokenService()
logger = logging.getLogger(__name__)

STATE_COOKIE = "tt_state"

@router.get("/login")
def login(request: Request):
    """
    Redirect to TikTok consent screen with a secure state cookie and PKCE (S256).

    Canonicalization:
    - If current request host/scheme doesn't match the configured TIKTOK_REDIRECT_URI host/scheme,
      redirect to the canonical /auth/login on that host first so cookies are set on the correct domain.
    - This prevents invalid_state caused by cookies being written on 192.168.x.x but callback hitting a FQDN (or vice versa).

    Note:
    - settings.TIKTOK_REDIRECT_URI must be whitelisted in TikTok Developer Console.
    """
    # Ensure cookies are created on the same host that will receive the callback
    cfg = urlparse(settings.TIKTOK_REDIRECT_URI)
    current_cb = urlparse(str(request.url_for("callback")))
    # Canonicalization disabled to avoid redirect loops behind reverse proxies.
    # We always set cookies on the host the user is visiting and use the configured
    # redirect_uri in the authorize URL to satisfy TikTok's whitelist.

    oauth = OAuthService()
    state = oauth.generate_state()
    verifier, challenge = oauth.generate_pkce_pair()

    # Optional query toggles to force showing consent screen:
    # /auth/login?force=1&prompt=consent
    force_q = (request.query_params.get("force", "") or "").lower()
    prompt_q = (request.query_params.get("prompt", "") or "")
    force_flag = force_q in {"1", "true", "yes", "y"}
    # Use the configured redirect_uri (must match TikTok whitelist)
    authorize_url = oauth.build_auth_url(
        state,
        code_challenge=challenge,
        force_revoke=force_flag,
        prompt=prompt_q or None,
    )
    resp = RedirectResponse(authorize_url, status_code=302)

    cookie_secure = (cfg.scheme == "https")
    # In production: consider setting 'domain' explicitly if serving on subdomains
    resp.set_cookie(
        key=STATE_COOKIE,
        value=state,
        max_age=600,
        httponly=True,
        samesite="lax",
        secure=cookie_secure,
        path="/",
    )
    resp.set_cookie(
        key="tt_pkce",
        value=verifier,
        max_age=600,
        httponly=True,
        samesite="lax",
        secure=cookie_secure,
        path="/",
    )
    logger.info(
        "OAuth login redirecting to TikTok authorize",
        extra={
            "authorize_url": authorize_url,
            "state_len": len(state),
            "pkce_verifier_len": len(verifier),
            "cookie_secure": cookie_secure,
            "request_host": request.headers.get("host"),
            "env": settings.ENV,
        },
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
    # Detailed state validation to diagnose issues in development
    missing_state_param = not bool(state)
    missing_cookie = not bool(cookie_state)
    mismatch_cookie = bool(state and cookie_state) and (cookie_state != state)
    invalid_signature = not bool(state and oauth.validate_state(state))

    # Strict check (production): require cookie match + valid signature
    # Relaxed check (development): allow valid HMAC state even if cookie missing/mismatch
    env_lower = (settings.ENV or "").lower()
    dev_mode = env_lower in {"dev", "development", "local"}

    if missing_state_param or invalid_signature or (not dev_mode and (missing_cookie or mismatch_cookie)):
        reason = {
            "missing_state_param": missing_state_param,
            "missing_cookie": missing_cookie,
            "mismatch_cookie": mismatch_cookie,
            "invalid_signature_or_expired": invalid_signature,
            "env": settings.ENV,
        }
        # Return structured detail to quickly pinpoint the cause
        raise HTTPException(status_code=400, detail=f"invalid_state:{reason}")

    if not code:
        raise HTTPException(status_code=400, detail="missing_code")

    client = TikTokClient()

    # Step 1: Exchange authorization code for tokens (fail hard if this step fails)
    try:
        pkce_verifier = request.cookies.get("tt_pkce")
        token_payload = await client.exchange_code_for_tokens(
            code,
            redirect_uri=settings.TIKTOK_REDIRECT_URI,
            code_verifier=pkce_verifier
        )
    except TikTokAPIError as e:
        logger.warning("OAuth token exchange failed", extra={"error": str(e)})
        raise HTTPException(status_code=502, detail=f"tiktok_api_error:token_exchange:{e}") from e
    except Exception as e:
        logger.exception("OAuth token exchange unexpected error")
        raise HTTPException(status_code=500, detail="token_exchange_failed") from e

    # Step 2: Best-effort fetch user info (do not fail overall flow if this step fails)
    access_token = token_payload.get("access_token", "")
    user_info = {"data": {"user": {}}}
    if access_token:
        try:
            user_info = await client.get_user_info(access_token)
        except TikTokAPIError as e:
            logger.warning("User info fetch failed; continuing", extra={"error": str(e)})
        except Exception:
            logger.exception("User info fetch unexpected error; continuing")

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
def auth_debug(request: Request):
    """
    Diagnostic endpoint to verify OAuth settings loaded by the running process
    and runtime-computed values that often cause OAuth redirects to fail.
    """
    oauth = OAuthService()
    computed_redirect_uri = str(request.url_for("callback"))
    # Example authorize URL (for inspection only; not for direct navigation)
    example_authorize_url = oauth.build_auth_url(
        state="debug_state_example",
    )
    return {
        "client_key": settings.TIKTOK_CLIENT_KEY,
        "configured_redirect_uri": settings.TIKTOK_REDIRECT_URI,
        "computed_redirect_uri": computed_redirect_uri,
        "scopes": settings.TIKTOK_SCOPES,
        "auth_base": settings.TIKTOK_AUTH_BASE_URL,
        "env": settings.ENV,
        "state_cookie_name": STATE_COOKIE,
        "example_authorize_url": example_authorize_url,
        "request_host": str(request.url.scheme) + "://" + request.headers.get("host", ""),
        "note": "Ensure you start OAuth from the SAME ORIGIN as configured_redirect_uri so cookies are present on callback.",
    }

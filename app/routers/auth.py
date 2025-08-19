from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from app.services.tiktok_client import get_tiktok_client
from app.core.config import get_settings
import secrets
import json
from pydantic import BaseModel
import logging
logging.basicConfig(level=logging.INFO)

router = APIRouter()
settings = get_settings()
tiktok = get_tiktok_client()

@router.get("/login")
async def login(request: Request, alt: int | None = None):
    """
    Stateless login: redirect to TikTok without setting cookies.
    Tokens will be returned at /auth/callback and stored on frontend (localStorage).
    - Compute redirect_uri dynamically from current request so local dev works (http://localhost:8110/auth/callback)
    - If `?alt=1` is passed, use alternate path (/v2/auth/authorize/) in case /v2/oauth/authorize/ returns 404 in some regions
    """
    from urllib.parse import urlencode, quote

    state = secrets.token_urlsafe(16)
    base = str(request.base_url).rstrip("/")
    redirect_uri = f"{base}/auth/callback"

    # TikTok expects space-delimited scopes
    scope_str = " ".join(settings.scopes_list)

    params = {
        "client_key": settings.TIKTOK_CLIENT_KEY,
        "response_type": "code",
        "scope": scope_str,
        "redirect_uri": redirect_uri,
        "state": state,
    }
    # Choose endpoint path: default oauth; alt=1 uses auth path
    path = "/v2/auth/authorize/" if alt else "/v2/oauth/authorize/"
    auth_url = f"{tiktok.auth_base}{path}?{urlencode(params, quote_via=quote)}"
    logging.info(f"Redirecting to TikTok auth URL: {auth_url}")
    return RedirectResponse(url=auth_url, status_code=302)

@router.get("/callback")
async def callback(request: Request, code: str | None = None, state: str | None = None):
    """
    Exchange code for tokens and return a small HTML page
    that stores tokens in localStorage then redirects to "/".
    - Uses the same redirect_uri used in /auth/login for consistency with TikTok validation
    """
    if not code:
        raise HTTPException(status_code=400, detail="missing code")

    base = str(request.base_url).rstrip("/")
    redirect_uri = f"{base}/auth/callback"

    try:
        token_res = await tiktok.exchange_token(code, redirect_uri=redirect_uri)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"token exchange failed: {e}")

    data = token_res.get("data") if isinstance(token_res, dict) else None
    if data is None:
        data = token_res if isinstance(token_res, dict) else {}

    access_token = data.get("access_token")
    refresh_token = data.get("refresh_token")
    open_id = data.get("open_id") or (data.get("user") or {}).get("open_id")

    payload = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "open_id": open_id,
    }

    html = """<!doctype html>
<html lang="en">
  <meta charset="utf-8">
  <title>Login Complete</title>
  <body style="font-family:system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; background:#111; color:#eee;">
    <div style="max-width:640px;margin:10vh auto;padding:20px;border:1px solid #2a2a2a;border-radius:12px;background:#181818;">
      <h2>เข้าสู่ระบบสำเร็จ</h2>
      <p>กำลังกลับไปยังหน้าเดิม...</p>
    </div>
    <script>
      (function(){
        const data = __DATA__;
        try {
          if (data && data.access_token) localStorage.setItem('tk_access', data.access_token);
          if (data && data.refresh_token) localStorage.setItem('tk_refresh', data.refresh_token);
          if (data && data.open_id) localStorage.setItem('tk_open_id', data.open_id);
        } catch (e) {}
        location.replace("/");
      })();
    </script>
  </body>
</html>
""".replace("__DATA__", json.dumps(payload))
    return HTMLResponse(content=html)

class RefreshReq(BaseModel):
    refresh_token: str

@router.post("/refresh")
async def refresh(payload: RefreshReq):
    """
    Stateless refresh: client sends refresh_token in JSON body and gets new tokens in JSON.
    """
    try:
        token_res = await tiktok.refresh_token(payload.refresh_token)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"refresh failed: {e}")

    data = token_res.get("data") if isinstance(token_res, dict) else None
    if data is None:
        data = token_res if isinstance(token_res, dict) else {}
    # Return as-is and also surface tokens at top-level for convenience
    result = {
        "data": data,
        "access_token": data.get("access_token"),
        "refresh_token": data.get("refresh_token"),
        "open_id": data.get("open_id") or (data.get("user") or {}).get("open_id"),
    }
    return JSONResponse(result)

@router.post("/logout")
async def logout():
    """
    Stateless logout: client clears its own storage; backend just acknowledges.
    """
    return {"message": "logged out"}

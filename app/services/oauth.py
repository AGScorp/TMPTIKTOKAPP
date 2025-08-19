from typing import Optional
from urllib.parse import urlencode
import time
import secrets
import hmac
import hashlib
import base64

from app.core.config import settings

class OAuthService:
    """
    Handles TikTok OAuth helper operations:
    - state generation/validation (HMAC-signed, short-lived)
    - building authorize URL
    Note: Token exchange/refresh/revoke will be implemented next.
    """

    def __init__(self) -> None:
        self.client_key = settings.TIKTOK_CLIENT_KEY
        self.redirect_uri = settings.TIKTOK_REDIRECT_URI
        self.scopes = settings.TIKTOK_SCOPES
        self.auth_base = settings.TIKTOK_AUTH_BASE_URL
        self.secret = settings.SECRET_KEY

    def _sign(self, payload: str) -> str:
        mac = hmac.new(self.secret.encode(), payload.encode(), hashlib.sha256).digest()
        return base64.urlsafe_b64encode(mac).decode().rstrip("=")

    def generate_state(self, ttl_seconds: int = 600) -> str:
        """
        Create a short-lived state string: "<ts>:<nonce>.<sig>"
        """
        ts = int(time.time())
        nonce = secrets.token_urlsafe(16)
        raw = f"{ts}:{nonce}"
        sig = self._sign(raw)
        return f"{raw}.{sig}"

    def validate_state(self, state: str, max_age_seconds: int = 600) -> bool:
        try:
            raw, sig = state.rsplit(".", 1)
        except ValueError:
            return False
        if not hmac.compare_digest(self._sign(raw), sig):
            return False
        try:
            ts_str, _ = raw.split(":", 1)
            ts = int(ts_str)
        except Exception:
            return False
        return (time.time() - ts) <= max_age_seconds

    def generate_pkce_pair(self) -> tuple[str, str]:
        """
        Generate PKCE code_verifier and code_challenge (S256).
        Returns (code_verifier, code_challenge).
        """
        # RFC 7636: code_verifier length 43-128 characters, unreserved charset
        verifier = secrets.token_urlsafe(64)[:128]
        digest = hashlib.sha256(verifier.encode()).digest()
        challenge = base64.urlsafe_b64encode(digest).decode().rstrip("=")
        return verifier, challenge

    def build_auth_url(
        self,
        state: str,
        code_challenge: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        force_revoke: Optional[bool] = None,
        prompt: Optional[str] = None,
    ) -> str:
        """
        Compose TikTok authorize URL. Adds PKCE if code_challenge provided.
        Optionally override redirect_uri for host/port flexibility.
        Supports forcing consent screen via:
          - settings.TIKTOK_FORCE_REVOKE or force_revoke=True -> adds revoke=1
          - settings.TIKTOK_PROMPT or prompt="consent"       -> adds prompt=consent
        """
        params = {
            "client_key": self.client_key,
            "response_type": "code",
            "redirect_uri": redirect_uri or self.redirect_uri,
            "scope": self.scopes,
            "state": state,
        }
        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"

        # Resolve effective flags (param overrides settings)
        eff_force = settings.TIKTOK_FORCE_REVOKE if force_revoke is None else bool(force_revoke)
        eff_prompt = (settings.TIKTOK_PROMPT or "").strip() if prompt is None else (prompt or "").strip()

        if eff_force:
            params["revoke"] = "1"
        if eff_prompt:
            params["prompt"] = eff_prompt

        return f"{self.auth_base}?{urlencode(params)}"

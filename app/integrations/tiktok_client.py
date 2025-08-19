from typing import Any, Dict, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings

class TikTokAPIError(Exception):
    pass

class TikTokClient:
    """
    Minimal TikTok API client.

    - OAuth: exchange authorization code for tokens (stubbed when client creds are missing)
    - Refresh/Revoke token support
    - Display API: user info
    - Next: content upload endpoints
    """
    def __init__(self) -> None:
        self.api_base = settings.TIKTOK_BASE_URL.rstrip("/")
        self.client_key = settings.TIKTOK_CLIENT_KEY
        self.client_secret = settings.TIKTOK_CLIENT_SECRET
        self.timeout = settings.HTTP_TIMEOUT_SECONDS

    def _is_dev_mode(self) -> bool:
        # Treat placeholders as "not configured" and allow dev stubs
        placeholder_keys = {"your_client_key", "your_client_secret"}
        if (not self.client_key or self.client_key in placeholder_keys
            or not self.client_secret or self.client_secret in placeholder_keys):
            return True
        # Also allow stubs in explicit development environment
        return (settings.ENV or "").lower() in {"dev", "development", "local"}

    def _token_url(self) -> str:
        # According to TikTok OpenAPI v2
        return f"{self.api_base}/oauth/token/"

    def _revoke_url(self) -> str:
        # According to TikTok OpenAPI v2
        return f"{self.api_base}/oauth/revoke/"

    def _user_info_url(self) -> str:
        # Display API - user info endpoint (path may vary by version/scope)
        return f"{self.api_base}/user/info/"

    @retry(
        reraise=True,
        stop=stop_after_attempt(max(1, settings.RATE_LIMIT_MAX_RETRIES)),
        wait=wait_exponential(
            multiplier=max(0.001, settings.RATE_LIMIT_BASE_DELAY_MS / 1000.0),
            max=max(0.001, settings.RATE_LIMIT_MAX_DELAY_MS / 1000.0),
        ),
        retry=retry_if_exception_type((httpx.HTTPError, TikTokAPIError)),
    )
    async def exchange_code_for_tokens(self, code: str, redirect_uri: Optional[str] = None, code_verifier: Optional[str] = None) -> Dict[str, Any]:
        """
        Exchange authorization code for access/refresh tokens.
        Dev-mode stub when app credentials are placeholders or ENV=development.
        """
        if self._is_dev_mode():
            return {
                "placeholder": True,
                "access_token": "dev_access_token",
                "refresh_token": "dev_refresh_token",
                "expires_in": 86400,
                "token_type": "Bearer",
                "scope": settings.TIKTOK_SCOPES,
            }

        payload = {
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri or settings.TIKTOK_REDIRECT_URI,
        }
        if code_verifier:
            payload["code_verifier"] = code_verifier

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            resp = await client.post(self._token_url(), data=payload, headers=headers)
            if resp.status_code == 429:
                # trigger retry/backoff
                raise TikTokAPIError("rate_limited")
            if resp.status_code >= 500:
                raise TikTokAPIError(f"server_error:{resp.status_code}")
            if resp.status_code >= 400:
                raise TikTokAPIError(f"bad_status:{resp.status_code}:{resp.text[:200]}")

            data = resp.json()
            # TikTok responses typically include an error object when failing
            if isinstance(data, dict) and data.get("error"):
                raise TikTokAPIError(str(data["error"]))
            return data

    @retry(
        reraise=True,
        stop=stop_after_attempt(max(1, settings.RATE_LIMIT_MAX_RETRIES)),
        wait=wait_exponential(
            multiplier=max(0.001, settings.RATE_LIMIT_BASE_DELAY_MS / 1000.0),
            max=max(0.001, settings.RATE_LIMIT_MAX_DELAY_MS / 1000.0),
        ),
        retry=retry_if_exception_type((httpx.HTTPError, TikTokAPIError)),
    )
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh_token.
        Dev-mode: return stubbed new access token.
        """
        if self._is_dev_mode() or (refresh_token or "").startswith("dev_"):
            return {
                "placeholder": True,
                "access_token": "dev_access_token_refreshed",
                "refresh_token": "dev_refresh_token_rotated",
                "expires_in": 86400,
                "token_type": "Bearer",
                "scope": settings.TIKTOK_SCOPES,
            }

        payload = {
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            resp = await client.post(self._token_url(), data=payload, headers=headers)
            if resp.status_code == 429:
                raise TikTokAPIError("rate_limited")
            if resp.status_code >= 500:
                raise TikTokAPIError(f"server_error:{resp.status_code}")
            if resp.status_code >= 400:
                raise TikTokAPIError(f"bad_status:{resp.status_code}:{resp.text[:200]}")
            data = resp.json()
            if isinstance(data, dict) and data.get("error"):
                raise TikTokAPIError(str(data["error"]))
            return data

    @retry(
        reraise=True,
        stop=stop_after_attempt(max(1, settings.RATE_LIMIT_MAX_RETRIES)),
        wait=wait_exponential(
            multiplier=max(0.001, settings.RATE_LIMIT_BASE_DELAY_MS / 1000.0),
            max=max(0.001, settings.RATE_LIMIT_MAX_DELAY_MS / 1000.0),
        ),
        retry=retry_if_exception_type((httpx.HTTPError, TikTokAPIError)),
    )
    async def revoke_token(self, access_token: str) -> Dict[str, Any]:
        """
        Revoke access token.
        Dev-mode: return stubbed success.
        """
        if self._is_dev_mode() or (access_token or "").startswith("dev_"):
            return {"placeholder": True, "revoked": True}

        payload = {
            "client_key": self.client_key,
            "token": access_token,
            "token_type_hint": "access_token",
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(self._revoke_url(), data=payload, headers=headers)
            if resp.status_code == 429:
                raise TikTokAPIError("rate_limited")
            if resp.status_code >= 500:
                raise TikTokAPIError(f"server_error:{resp.status_code}")
            if resp.status_code >= 400:
                raise TikTokAPIError(f"bad_status:{resp.status_code}:{resp.text[:200]}")
            data = resp.json()
            if isinstance(data, dict) and data.get("error"):
                raise TikTokAPIError(str(data["error"]))
            return data

    @retry(
        reraise=True,
        stop=stop_after_attempt(max(1, settings.RATE_LIMIT_MAX_RETRIES)),
        wait=wait_exponential(
            multiplier=max(0.001, settings.RATE_LIMIT_BASE_DELAY_MS / 1000.0),
            max=max(0.001, settings.RATE_LIMIT_MAX_DELAY_MS / 1000.0),
        ),
        retry=retry_if_exception_type((httpx.HTTPError, TikTokAPIError)),
    )
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Return TikTok user info using Display API scopes.
        Dev-mode stub when app credentials are placeholders/ENV=development or when the token starts with 'dev_'.
        """
        if self._is_dev_mode() or (access_token or "").startswith("dev_"):
            return {
                "placeholder": True,
                "data": {
                    "user": {
                        "open_id": "dev_open_id_123",
                        "display_name": "Dev User",
                        "profile_image_url": "https://example.com/dev_profile.jpg",
                        "stats": {"follower_count": 0, "following_count": 0, "likes_count": 0, "video_count": 0},
                    }
                }
            }

        headers = {
            "Authorization": f"Bearer {access_token}",
        }
        params = {
            "fields": ",".join([
                "open_id",
                "display_name",
                "profile_image_url",
                "follower_count",
                "following_count",
                "likes_count",
                "video_count",
            ])
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(self._user_info_url(), headers=headers, params=params)
            if resp.status_code == 429:
                raise TikTokAPIError("rate_limited")
            if resp.status_code >= 500:
                raise TikTokAPIError(f"server_error:{resp.status_code}")
            if resp.status_code >= 400:
                raise TikTokAPIError(f"bad_status:{resp.status_code}:{resp.text[:200]}")

            data = resp.json()
            if isinstance(data, dict) and data.get("error"):
                raise TikTokAPIError(str(data["error"]))
            return data

    @retry(
        reraise=True,
        stop=stop_after_attempt(max(1, settings.RATE_LIMIT_MAX_RETRIES)),
        wait=wait_exponential(
            multiplier=max(0.001, settings.RATE_LIMIT_BASE_DELAY_MS / 1000.0),
            max=max(0.001, settings.RATE_LIMIT_MAX_DELAY_MS / 1000.0),
        ),
        retry=retry_if_exception_type((httpx.HTTPError, TikTokAPIError)),
    )
    async def get_client_access_token(self) -> Dict[str, Any]:
        """
        Obtain an app-level client access token (client_credentials).
        Dev-mode: returns a stub token for local development.
        """
        if self._is_dev_mode():
            return {
                "placeholder": True,
                "access_token": "dev_client_access_token",
                "expires_in": 3600,
                "token_type": "Bearer",
                "scope": "",
            }

        payload = {
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            resp = await client.post(self._token_url(), data=payload, headers=headers)
            if resp.status_code == 429:
                raise TikTokAPIError("rate_limited")
            if resp.status_code >= 500:
                raise TikTokAPIError(f"server_error:{resp.status_code}")
            if resp.status_code >= 400:
                raise TikTokAPIError(f"bad_status:{resp.status_code}:{resp.text[:200]}")
            data = resp.json()
            if isinstance(data, dict) and data.get("error"):
                raise TikTokAPIError(str(data["error"]))
            return data

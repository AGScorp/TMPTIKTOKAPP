import httpx
from typing import Any, Dict, List, Optional
from app.core.config import get_settings

settings = get_settings()

AUTH_BASE_URL = settings.TIKTOK_AUTH_BASE_URL.rstrip("/")
API_BASE_URL = settings.TIKTOK_BASE_URL.rstrip("/")


class TikTokClient:
    def __init__(self) -> None:
        self.api_base = API_BASE_URL
        self.auth_base = AUTH_BASE_URL

    # ---------- OAuth ----------

    def build_authorize_url(self, state: str, redirect_uri: Optional[str] = None, scopes: Optional[str] = None) -> str:
        """
        สร้าง URL สำหรับ redirect ไปหน้าอนุญาต TikTok
        Docs: https://developers.tiktok.com/doc/tiktok-api-v2-authenticate-with-tiktok/
        """
        from urllib.parse import urlencode, quote

        redir = redirect_uri or settings.TIKTOK_REDIRECT_URI
        scope_str = scopes or settings.TIKTOK_SCOPES
        params = {
            "client_key": settings.TIKTOK_CLIENT_KEY,
            "response_type": "code",
            "scope": scope_str,
            "redirect_uri": redir,
            "state": state,
        }
        # TikTok OAuth v2 endpoint (correct path)
        return f"{self.auth_base}/v2/oauth/authorize/?{urlencode(params, quote_via=quote)}"

    async def exchange_token(self, code: str, redirect_uri: Optional[str] = None) -> Dict[str, Any]:
        """
        แลก code เป็น access_token/refresh_token
        Endpoint: POST {API_BASE_URL}/oauth/token/
        Content-Type: application/x-www-form-urlencoded
        """
        url = f"{self.api_base}/oauth/token/"
        redir = redirect_uri or settings.TIKTOK_REDIRECT_URI
        data = {
            "client_key": settings.TIKTOK_CLIENT_KEY,
            "client_secret": settings.TIKTOK_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redir,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
            r.raise_for_status()
            return r.json()

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        รีเฟรช access_token ด้วย refresh_token
        """
        url = f"{self.api_base}/oauth/token/"
        data = {
            "client_key": settings.TIKTOK_CLIENT_KEY,
            "client_secret": settings.TIKTOK_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
            r.raise_for_status()
            return r.json()

    # ---------- User ----------

    async def get_user_info(self, access_token: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        ดึงข้อมูลผู้ใช้ปัจจุบัน
        PHP ref: [User.getSelf()](ref/User/User.php:66)
        GET {API_BASE_URL}/user/info/?fields=...
        """
        if fields is None:
            fields = [
                "open_id",
                "display_name",
                "profile_deep_link",
                "avatar_url",
                "avatar_large_url",
                "is_verified",
                "follower_count",
                "following_count",
                "likes_count",
                "video_count",
                "union_id",
            ]
        url = f"{self.api_base}/user/info/"
        params = {"fields": ",".join(fields)}
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(url, params=params, headers=headers)
            r.raise_for_status()
            return r.json()

    # ---------- Video ----------

    def _default_video_fields(self) -> List[str]:
        return [
            "id",
            "create_time",
            "title",
            "cover_image_url",
            "share_url",
            "video_description",
            "duration",
            "height",
            "width",
            "embed_html",
            "embed_link",
            "like_count",
            "comment_count",
            "share_count",
            "view_count",
        ]

    async def list_videos(
        self,
        access_token: str,
        cursor: Optional[str] = None,
        max_count: int = 20,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        ดึงรายการวิดีโอของผู้ใช้
        PHP ref: [Video.getList()](ref/Video/Video.php:93)
        POST {API_BASE_URL}/video/list/?fields=...
        body: { "cursor": "...", "max_count": 20 }
        """
        if fields is None:
            fields = self._default_video_fields()
        url = f"{self.api_base}/video/list/"
        params = {"fields": ",".join(fields)}
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        body: Dict[str, Any] = {}
        if cursor:
            body["cursor"] = cursor
        if max_count:
            body["max_count"] = max_count

        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(url, params=params, data=body, headers=headers)
            r.raise_for_status()
            return r.json()

    async def query_videos(
        self,
        access_token: str,
        video_ids: List[str],
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        ตรวจสอบวิดีโอตาม video_ids
        PHP ref: [Video.query()](ref/Video/Video.php:119)
        POST {API_BASE_URL}/video/query/?fields=...
        body: { "filters": "{\"video_ids\": [\"vid1\",\"vid2\"]}" }
        """
        if fields is None:
            fields = self._default_video_fields()
        url = f"{self.api_base}/video/query/"
        params = {"fields": ",".join(fields)}
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        # ตาม PHP ref ใช้ json encode ในฟิลด์ filters
        import json

        body = {
            "filters": json.dumps({"video_ids": video_ids}),
        }

        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(url, params=params, data=body, headers=headers)
            r.raise_for_status()
            return r.json()


# dependency factory
def get_tiktok_client() -> TikTokClient:
    return TikTokClient()
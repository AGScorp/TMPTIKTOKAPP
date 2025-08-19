from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.services.tiktok_client import get_tiktok_client

router = APIRouter()

# Stateless auth: expect Bearer token in Authorization header


def _require_token(request: Request) -> str:
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    return auth.split(" ", 1)[1].strip()


@router.get("/me")
async def get_me(request: Request):
    """
    ดึงข้อมูลผู้ใช้ปัจจุบันจาก TikTok
    อ้างอิง: [User.getSelf()](ref/User/User.php:66)
    """
    token = _require_token(request)
    tiktok = get_tiktok_client()
    return await tiktok.get_user_info(token)


class VideosListReq(BaseModel):
    cursor: Optional[str] = None
    max_count: int = 20
    fields: Optional[List[str]] = None


@router.post("/videos")
async def list_videos(request: Request, payload: VideosListReq):
    """
    ดึงรายการวิดีโอของผู้ใช้
    อ้างอิง: [Video.getList()](ref/Video/Video.php:93)
    """
    token = _require_token(request)
    tiktok = get_tiktok_client()
    return await tiktok.list_videos(
        access_token=token,
        cursor=payload.cursor,
        max_count=payload.max_count,
        fields=payload.fields,
    )


class VideosQueryReq(BaseModel):
    video_ids: List[str]
    fields: Optional[List[str]] = None


@router.post("/videos/query")
async def query_videos(request: Request, payload: VideosQueryReq):
    """
    ตรวจสอบวิดีโอตามรายการ video_ids
    อ้างอิง: [Video.query()](ref/Video/Video.php:119)
    """
    token = _require_token(request)
    tiktok = get_tiktok_client()
    return await tiktok.query_videos(
        access_token=token,
        video_ids=payload.video_ids,
        fields=payload.fields,
    )
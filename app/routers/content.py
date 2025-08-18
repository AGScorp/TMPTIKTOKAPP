from __future__ import annotations

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional

from app.services.content import ContentService
from app.core.config import settings

router = APIRouter()
content_service = ContentService()

def _allowed_url(url: str) -> bool:
    prefixes = [p.strip() for p in (settings.CONTENT_ALLOWED_URL_PREFIXES or "").split(",") if p.strip()]
    if not prefixes:
        # If not configured, reject for safety
        return False
    return any(url.startswith(p) for p in prefixes)

@router.get("/debug")
def debug():
    """
    Content module diagnostics: shows current whitelist prefixes loaded from settings.
    """
    prefixes = [p.strip() for p in (settings.CONTENT_ALLOWED_URL_PREFIXES or "").split(",") if p.strip()]
    return {"whitelist_prefixes": prefixes}

@router.post("/upload/file")
async def upload_file(
    file: UploadFile = File(...),
    publish_mode: str = Form("draft"),  # public|friends|self|draft
):
    """
    Upload a media file to TikTok (dev-stub behavior). In production, this would:
    - initiate upload session -> upload chunks -> commit -> return job id/asset id
    """
    try:
        # Dev stub: read few bytes to ensure file arrives
        head = await file.read(1024)
        job = await content_service.create_local_file_job(filename=file.filename or "upload.bin", first_chunk=head, publish_mode=publish_mode)
        return JSONResponse({"message": "upload_file_accepted", "job": job})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"upload_file_failed:{e}")

@router.post("/upload/url")
async def upload_url(
    source_url: str = Form(...),
    publish_mode: str = Form("draft"),  # public|friends|self|draft
):
    """
    Create a job that pulls media from a whitelisted URL prefix (required by TikTok domain verification).
    """
    if not _allowed_url(source_url):
        raise HTTPException(status_code=400, detail="source_url_not_whitelisted")
    try:
        job = await content_service.create_pull_by_url_job(source_url=source_url, publish_mode=publish_mode)
        return JSONResponse({"message": "upload_url_job_created", "job": job})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"upload_url_failed:{e}")

@router.get("/status/{job_id}")
async def status(job_id: str):
    """
    Check status of an upload/publish job (dev-stub).
    """
    try:
        st = await content_service.get_status(job_id)
        return JSONResponse({"job_id": job_id, "status": st})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"status_check_failed:{e}")

@router.post("/publish")
async def publish(
    job_id: str = Form(...),
    privacy: str = Form("draft"),  # public|friends|self|draft
    caption: Optional[str] = Form(None),
):
    """
    Publish a previously uploaded asset or move it to drafts (dev-stub).
    """
    try:
        res = await content_service.publish(job_id=job_id, privacy=privacy, caption=caption)
        return JSONResponse({"message": "publish_enqueued", "result": res})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"publish_failed:{e}")

@router.get("/creator-info")
async def creator_info(access_token: Optional[str] = Query(None)):
    """
    Fetch creator info and allowed privacy options (dev-stub path without real TikTok creds).
    """
    try:
        info = await content_service.fetch_creator_info(access_token=access_token)
        return JSONResponse(info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"creator_info_failed:{e}")

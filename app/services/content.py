# Content service for upload orchestration, status polling, publish/draft (dev stubs).
from __future__ import annotations

import time
import uuid
from typing import Any, Dict, Optional

from app.integrations.tiktok_client import TikTokClient

class ContentService:
    """
    Dev-mode stub implementation that mimics content upload/URL pull/publish flows.
    When moving to production, replace internal in-memory state with DB-backed jobs and
    real TikTok Content Posting API calls.
    """

    # In-memory job store for dev-mode
    _jobs: Dict[str, Dict[str, Any]] = {}

    def __init__(self) -> None:
        self.client = TikTokClient()

    async def create_local_file_job(self, filename: str, first_chunk: bytes, publish_mode: str = "draft") -> Dict[str, Any]:
        """
        Accept a local file upload and create a dev job.
        """
        job_id = str(uuid.uuid4())
        job = {
            "id": job_id,
            "source_type": "local",
            "filename": filename,
            "size_hint": len(first_chunk),
            "publish_mode": publish_mode,
            "status": "pending",
            "created_at": int(time.time()),
        }
        self._jobs[job_id] = job
        # Simulate background progression
        await self._progress(job_id, to_status="processing")
        return job

    async def create_pull_by_url_job(self, source_url: str, publish_mode: str = "draft") -> Dict[str, Any]:
        """
        Create a dev job to pull media by URL.
        """
        job_id = str(uuid.uuid4())
        job = {
            "id": job_id,
            "source_type": "url",
            "source_url": source_url,
            "publish_mode": publish_mode,
            "status": "pending",
            "created_at": int(time.time()),
        }
        self._jobs[job_id] = job
        await self._progress(job_id, to_status="processing")
        return job

    async def get_status(self, job_id: str) -> Dict[str, Any]:
        """
        Return current job status or not_found.
        """
        job = self._jobs.get(job_id)
        if not job:
            return {"state": "not_found"}
        # Simulate completion after some time
        if job["status"] == "processing" and (int(time.time()) - job["created_at"]) > 2:
            job["status"] = "completed"
            job["tiktok_asset_id"] = f"dev_asset_{job_id[:8]}"
        return {"state": job["status"], "asset_id": job.get("tiktok_asset_id")}

    async def publish(self, job_id: str, privacy: str = "draft", caption: Optional[str] = None) -> Dict[str, Any]:
        """
        Simulate publish/draft operation. In production, this would call TikTok publish endpoints.
        """
        job = self._jobs.get(job_id)
        if not job:
            return {"ok": False, "reason": "job_not_found"}
        if job.get("status") != "completed":
            return {"ok": False, "reason": "not_completed"}
        # Simulate publish success
        return {
            "ok": True,
            "privacy": privacy,
            "caption": caption,
            "asset_id": job.get("tiktok_asset_id"),
            "published_at": int(time.time()),
        }

    async def fetch_creator_info(self, access_token: Optional[str]) -> Dict[str, Any]:
        """
        Retrieve creator info via Display API. In dev-mode, returns a stub.
        """
        token = access_token or "dev_access_token"
        return await self.client.get_user_info(token)

    async def _progress(self, job_id: str, to_status: str = "processing") -> None:
        """
        Internal helper to bump job status; in real implementation this would run in background worker.
        """
        job = self._jobs.get(job_id)
        if not job:
            return
        job["status"] = to_status

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.exc import SQLAlchemyError

from app.db.session import SessionLocal
from app.db.models import TikTokUser
from app.core.security import encrypt_blob
from app.core.config import settings


class TokenService:
    """
    Persist and manage TikTok user tokens securely (encrypted at rest).
    - save_user_tokens: upsert by open_id with encrypted access/refresh tokens
    - compute expires_at from expires_in
    """

    def __init__(self) -> None:
        pass

    def _compute_expiry(self, expires_in: Optional[int]) -> Optional[datetime]:
        if not expires_in:
            return None
        return datetime.utcnow() + timedelta(seconds=int(expires_in))

    def save_user_tokens(
        self,
        user_info: Dict[str, Any],
        token_payload: Dict[str, Any],
    ) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Store tokens and basic profile info.
        Returns (persisted, user_id, error_message)
        Does not raise on DB errors; returns error message for caller to surface if needed.
        Expected user_info:
          {
            "data": {
              "user": {
                "open_id": "...",
                "display_name": "...",
                "profile_image_url": "..."
              }
            }
          }
        token_payload expected fields:
          access_token, refresh_token, token_type, scope, expires_in
        """
        # Extract open_id and basic profile
        try:
            user_data = (user_info or {}).get("data", {}).get("user", {})
            open_id = user_data.get("open_id") or user_data.get("openId") or "unknown_open_id"
            display_name = user_data.get("display_name")
            profile_image_url = user_data.get("profile_image_url")
        except Exception:
            # fallback if shape different (e.g., dev stub)
            open_id = "unknown_open_id"
            display_name = None
            profile_image_url = None

        access_token = token_payload.get("access_token", "")
        refresh_token = token_payload.get("refresh_token", "")
        token_type = token_payload.get("token_type")
        scope = token_payload.get("scope")
        expires_in = token_payload.get("expires_in")

        # Encrypt token blobs
        enc_access = encrypt_blob(access_token.encode()) if access_token else None
        enc_refresh = encrypt_blob(refresh_token.encode()) if refresh_token else None
        expires_at = self._compute_expiry(expires_in)

        db = None
        try:
            db = SessionLocal()
            # Upsert by tiktok_open_id
            existing: Optional[TikTokUser] = db.query(TikTokUser).filter(
                TikTokUser.tiktok_open_id == open_id
            ).one_or_none()

            if existing:
                existing.display_name = display_name
                existing.profile_image_url = profile_image_url
                existing.access_token = enc_access
                existing.refresh_token = enc_refresh
                existing.token_type = token_type
                existing.scope = scope
                existing.expires_at = expires_at
                existing.last_refreshed_at = datetime.utcnow()
                db.add(existing)
                db.commit()
                db.refresh(existing)
                return True, existing.id, None
            else:
                new_user = TikTokUser(
                    tiktok_open_id=open_id,
                    display_name=display_name,
                    profile_image_url=profile_image_url,
                    access_token=enc_access,
                    refresh_token=enc_refresh,
                    token_type=token_type,
                    scope=scope,
                    expires_at=expires_at,
                    last_refreshed_at=datetime.utcnow(),
                )
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                return True, new_user.id, None
        except SQLAlchemyError as e:
            # Do not raise; return error to caller
            return False, None, f"db_error:{str(e.__class__.__name__)}"
        except Exception as e:
            return False, None, f"persist_error:{e}"
        finally:
            if db is not None:
                db.close()

from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, LargeBinary, Text, Index

class Base(DeclarativeBase):
    pass

class TikTokUser(Base):
    __tablename__ = "tiktok_users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tiktok_open_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(255))
    profile_image_url: Mapped[str | None] = mapped_column(Text)

    # Token storage (encrypted)
    access_token: Mapped[bytes | None] = mapped_column(LargeBinary)
    refresh_token: Mapped[bytes | None] = mapped_column(LargeBinary)
    token_type: Mapped[str | None] = mapped_column(String(32))
    scope: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_refreshed_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_users_openid", "tiktok_open_id"),
    )

class UploadJob(Base):
    __tablename__ = "upload_jobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    source_type: Mapped[str] = mapped_column(String(16))  # local | url
    source_url: Mapped[str | None] = mapped_column(Text)
    file_path: Mapped[str | None] = mapped_column(Text)

    tiktok_asset_id: Mapped[str | None] = mapped_column(String(128), index=True)
    publish_mode: Mapped[str] = mapped_column(String(24), default="draft")  # public|friends|self|draft
    status: Mapped[str] = mapped_column(String(24), default="pending")      # pending|processing|completed|failed
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    error_detail: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_jobs_user_status", "user_id", "status"),
    )

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event: Mapped[str] = mapped_column(String(64), index=True)
    request_id: Mapped[str | None] = mapped_column(String(64), index=True)
    detail: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

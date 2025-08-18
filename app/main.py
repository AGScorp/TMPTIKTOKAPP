from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
import logging

from app.core.config import settings
from app.core.logging import configure_logging
from app.middleware.errors import add_error_handlers
from app.middleware.observability import RequestContextMiddleware
from app.middleware.security import SecurityHeadersMiddleware

# DB metadata for optional auto-create in dev
from app.db.session import engine
from app.db.models import Base

logger = logging.getLogger(__name__)

configure_logging()

app = FastAPI(title=settings.APP_NAME)

# Middleware
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)

# Error handlers
add_error_handlers(app)

# Static files (for frontend assets)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Routers
from app.routers import auth, content, display, web
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(content.router, prefix="/content", tags=["content"])
app.include_router(display.router, prefix="/display", tags=["display"])
app.include_router(web.router, tags=["web"])

@app.on_event("startup")
def on_startup() -> None:
    # Best effort: create tables in dev; in prod use Alembic migrations
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables are ensured (create_all).")
    except Exception:
        logger.exception("Failed to ensure database tables. Run migrations or check DATABASE_URL.")

@app.get("/health")
def health():
    return {"status": "ok"}

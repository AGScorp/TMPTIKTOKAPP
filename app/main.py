from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from app.core.config import get_settings
from urllib.parse import urlparse
import os

app = FastAPI(title="holoApp", version="0.1.0")

settings = get_settings()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",  # อนุญาตทุก origin เพื่อให้ frontend ติดต่อ backend ได้แม้ต่างโดเมน
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
if os.path.isdir("web"):
    app.mount("/static", StaticFiles(directory="web"), name="static")

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/")
def root():
    index_path = os.path.join("web", "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    return JSONResponse({"message": "holoApp backend is running. Create web/index.html to serve UI.", "docs": "/docs"})

# Include routers if available
try:
    from app.routers import auth, videos
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(videos.router, prefix="/api", tags=["api"])
except Exception:
    # Routers may not exist yet during initial setup
    pass
@app.get("/config")
def public_config(request: Request):
    # ส่งค่า public config จาก .env ให้ frontend ใช้งาน (ไม่รวม secret)
    base_url = str(request.base_url)
    return {
        "api_base_url": base_url,
        "host": settings.HOST,
        "port": settings.PORT,
        "tiktok": {
            "auth_base_url": settings.TIKTOK_AUTH_BASE_URL,
            "redirect_uri": settings.TIKTOK_REDIRECT_URI,
            "scopes": settings.scopes_list,
            "base_url": settings.TIKTOK_BASE_URL,
            "client_key": settings.TIKTOK_CLIENT_KEY,
        },
    }
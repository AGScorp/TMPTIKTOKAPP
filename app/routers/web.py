from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    """
    Simple dashboard landing page.
    - Token input and helper actions
    - Quick links to features
    """
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/content", response_class=HTMLResponse)
def content_page(request: Request):
    """
    Content workflow page rendered within the unified dashboard.
    """
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request):
    """
    Profile viewer page rendered within the unified dashboard.
    """
    return templates.TemplateResponse("index.html", {"request": request})
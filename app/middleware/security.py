from __future__ import annotations

from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds minimal security headers suitable for API responses.
    In production behind HTTPS and a proper proxy/cdn, you may harden further (HSTS, CSP, etc.)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Basic clickjacking protection
        response.headers.setdefault("X-Frame-Options", "DENY")
        # Disable MIME type sniffing
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        # Referrer policy
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        # Cross-Origin-Opener for isolation (optional; comment out if it breaks embedding flows)
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        # Cross-Origin-Resource-Policy
        response.headers.setdefault("Cross-Origin-Resource-Policy", "same-site")

        # HSTS: enable only when HTTPS is enforced in production
        # response.headers.setdefault("Strict-Transport-Security", "max-age=63072000; includeSubDomains; preload")

        # Example CSP (relaxed): adapt for your UI/static host if serving HTML
        # response.headers.setdefault("Content-Security-Policy", "default-src 'self'")

        return response
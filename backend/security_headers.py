"""
Security headers middleware.
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach recommended HTTP security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        if not settings.enable_security_headers:
            return response

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https: http:; "
            "frame-ancestors 'none'"
        )

        request_proto = request.headers.get("x-forwarded-proto", request.url.scheme)
        if request_proto == "https":
            response.headers["Strict-Transport-Security"] = f"max-age={settings.hsts_max_age_seconds}; includeSubDomains"

        return response

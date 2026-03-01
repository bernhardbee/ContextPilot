"""
Security middleware and utilities for ContextPilot.
"""
import hashlib
import hmac
import time
from typing import Optional
from fastapi import HTTPException, Security, status, Header, Request
from fastapi.security import APIKeyHeader
from config import settings
from logger import logger


# API Key header authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def build_signature_payload(method: str, path: str, timestamp: str, body: bytes) -> bytes:
    """Build canonical payload bytes used for signature generation/verification."""
    body_hash = hashlib.sha256(body).hexdigest()
    canonical = "\n".join([method.upper(), path, timestamp, body_hash])
    return canonical.encode("utf-8")


def generate_request_signature(method: str, path: str, timestamp: str, body: bytes, secret: str) -> str:
    """Generate HMAC-SHA256 request signature."""
    payload = build_signature_payload(method=method, path=path, timestamp=timestamp, body=body)
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def is_timestamp_fresh(timestamp: str, max_age_seconds: int) -> bool:
    """Validate signature timestamp age to reduce replay risk."""
    try:
        timestamp_value = int(timestamp)
    except (TypeError, ValueError):
        return False
    current_time = int(time.time())
    return abs(current_time - timestamp_value) <= max_age_seconds


async def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """
    Verify API key if authentication is enabled.
    
    Args:
        api_key: API key from request header
        
    Returns:
        Validated API key
        
    Raises:
        HTTPException: If authentication is enabled and key is invalid
    """
    if not settings.enable_auth:
        return "auth_disabled"
    
    if not api_key:
        logger.warning("API request without API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    if api_key != settings.api_key:
        logger.warning(f"Invalid API key attempt: {api_key[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return api_key


async def verify_request_signature(
    request: Request,
    x_request_signature: Optional[str] = Header(default=None, alias="X-Request-Signature"),
    x_request_timestamp: Optional[str] = Header(default=None, alias="X-Request-Timestamp"),
) -> str:
    """Verify signed requests for configured mutating HTTP methods."""
    if not settings.enable_request_signing:
        return "request_signing_disabled"

    enforced_methods = [method.upper() for method in settings.request_signing_methods]
    if request.method.upper() not in enforced_methods:
        return "request_signing_not_required"

    signing_secret = settings.request_signing_secret.strip()
    if not signing_secret:
        logger.error("Request signing is enabled but CONTEXTPILOT_REQUEST_SIGNING_SECRET is not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Request signing is misconfigured"
        )

    if not x_request_signature or not x_request_timestamp:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing request signature headers"
        )

    if not is_timestamp_fresh(x_request_timestamp, settings.request_signing_max_age_seconds):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Request signature timestamp is invalid or expired"
        )

    request_body = await request.body()
    expected_signature = generate_request_signature(
        method=request.method,
        path=request.url.path,
        timestamp=x_request_timestamp,
        body=request_body,
        secret=signing_secret,
    )
    if not hmac.compare_digest(x_request_signature, expected_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid request signature"
        )

    return "request_signature_valid"

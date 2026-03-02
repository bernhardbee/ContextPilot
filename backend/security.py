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
from monitoring import record_security_event
from security_audit import persist_security_event


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


def hash_api_key(api_key: str) -> str:
    """Return SHA256 hash for API key values."""
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def verify_api_key_against_hash(api_key: str, expected_hash: str) -> bool:
    """Constant-time comparison between API key and expected SHA256 hash."""
    computed_hash = hash_api_key(api_key)
    return hmac.compare_digest(computed_hash, expected_hash)


def is_timestamp_fresh(timestamp: str, max_age_seconds: int) -> bool:
    """Validate signature timestamp age to reduce replay risk."""
    try:
        timestamp_value = int(timestamp)
    except (TypeError, ValueError):
        return False
    current_time = int(time.time())
    return abs(current_time - timestamp_value) <= max_age_seconds


async def verify_api_key(api_key: Optional[str] = Security(api_key_header), request: Request = None) -> str:
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
        record_security_event(event="api_key_auth", outcome="missing_key")
        persist_security_event(event="api_key_auth", outcome="missing_key", request=request)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )

    expected_plain = settings.api_key.strip() if isinstance(settings.api_key, str) else ""
    expected_hash = settings.api_key_hash.strip() if isinstance(settings.api_key_hash, str) else ""

    if not expected_hash:
        try:
            import settings_store as settings_store_module
            if settings_store_module.settings_store:
                persisted_hash = settings_store_module.settings_store.get("api_key_hash")
                if persisted_hash:
                    expected_hash = persisted_hash.strip()
                    settings.api_key_hash = expected_hash
        except Exception:
            pass

    plain_match = bool(expected_plain) and hmac.compare_digest(api_key, expected_plain)
    hash_match = bool(expected_hash) and verify_api_key_against_hash(api_key, expected_hash)

    if not plain_match and not hash_match:
        logger.warning(f"Invalid API key attempt: {api_key[:8]}...")
        record_security_event(event="api_key_auth", outcome="invalid_key")
        persist_security_event(
            event="api_key_auth",
            outcome="invalid_key",
            request=request,
            actor=f"api_key:{api_key[:8]}***"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    record_security_event(event="api_key_auth", outcome="valid_key")
    persist_security_event(
        event="api_key_auth",
        outcome="valid_key",
        request=request,
        actor=f"api_key:{api_key[:8]}***"
    )

    try:
        import settings_store as settings_store_module
        if settings_store_module.settings_store:
            now_ts = str(int(time.time()))
            settings_store_module.settings_store.set("api_key_last_used_at", now_ts)
            if not settings_store_module.settings_store.get("api_key_created_at"):
                settings_store_module.settings_store.set("api_key_created_at", now_ts)
    except Exception:
        pass
    
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
        record_security_event(event="request_signing", outcome="misconfigured")
        persist_security_event(event="request_signing", outcome="misconfigured", request=request)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Request signing is misconfigured"
        )

    if not x_request_signature or not x_request_timestamp:
        record_security_event(event="request_signing", outcome="missing_headers")
        persist_security_event(event="request_signing", outcome="missing_headers", request=request)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing request signature headers"
        )

    if not is_timestamp_fresh(x_request_timestamp, settings.request_signing_max_age_seconds):
        record_security_event(event="request_signing", outcome="invalid_timestamp")
        persist_security_event(event="request_signing", outcome="invalid_timestamp", request=request)
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
        record_security_event(event="request_signing", outcome="invalid_signature")
        persist_security_event(event="request_signing", outcome="invalid_signature", request=request)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid request signature"
        )

    record_security_event(event="request_signing", outcome="valid_signature")
    persist_security_event(event="request_signing", outcome="valid_signature", request=request)

    return "request_signature_valid"

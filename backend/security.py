"""
Security middleware and utilities for ContextPilot.
"""
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from config import settings
from logger import logger


# API Key header authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


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

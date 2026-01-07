"""
Input validation utilities for ContextPilot.
"""
import re
from typing import List
from fastapi import HTTPException, status
from config import settings


def validate_content_length(content: str) -> None:
    """
    Validate content length is within limits.
    
    Args:
        content: Content to validate
        
    Raises:
        HTTPException: If content exceeds maximum length
    """
    if len(content) > settings.max_content_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Content exceeds maximum length of {settings.max_content_length} characters"
        )
    
    if not content or not content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content cannot be empty"
        )


def validate_tags(tags: List[str]) -> None:
    """
    Validate tags are within limits and properly formatted.
    
    Args:
        tags: List of tags to validate
        
    Raises:
        HTTPException: If tags are invalid
    """
    if len(tags) > settings.max_tag_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {settings.max_tag_count} tags allowed"
        )
    
    for tag in tags:
        if not tag or not tag.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tags cannot be empty"
            )
        
        if len(tag) > settings.max_tag_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tag '{tag}' exceeds maximum length of {settings.max_tag_length} characters"
            )
        
        # Only allow alphanumeric, spaces, hyphens, and underscores
        if not re.match(r'^[\w\s\-]+$', tag):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tag '{tag}' contains invalid characters. Only alphanumeric, spaces, hyphens, and underscores allowed"
            )


def sanitize_string(text: str) -> str:
    """
    Sanitize string input by removing potentially harmful characters.
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text
    """
    # Remove null bytes and control characters except newlines and tabs
    sanitized = ''.join(char for char in text if char == '\n' or char == '\t' or ord(char) >= 32)
    return sanitized.strip()

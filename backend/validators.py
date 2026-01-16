"""
Input validation utilities for ContextPilot.
"""
import json
import re
from pathlib import Path
from typing import Dict, List
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


def load_valid_models() -> Dict[str, List[str]]:
    """Load valid models from JSON file."""
    models_file = Path(__file__).parent / "valid_models.json"
    try:
        with open(models_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Fallback to hardcoded models if file is missing or invalid
        return {
            "openai": [
                "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4-turbo-preview",
                "gpt-4", "gpt-3.5-turbo", "gpt-3.5-turbo-16k"
            ],
            "anthropic": [
                "claude-3-5-sonnet-20241022", "claude-3-5-sonnet-20240620", 
                "claude-3-opus-20240229", "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307"
            ],
            "ollama": []
        }


def validate_ai_model(provider: str, model: str) -> None:
    """
    Validate AI model name is supported for the given provider.
    
    Args:
        provider: AI provider ("openai", "anthropic", "ollama")
        model: Model name to validate
        
    Raises:
        HTTPException: If model is not supported for the provider
    """
    valid_models = load_valid_models()
    
    if provider in ["openai", "anthropic"]:
        if model not in valid_models[provider]:
            valid_models_str = ", ".join(valid_models[provider])
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model '{model}' is not supported for provider '{provider}'. Valid models: {valid_models_str}"
            )

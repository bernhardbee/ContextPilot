"""
Configuration management for ContextPilot backend.
"""
import os
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    
    # CORS Configuration
    cors_origins: List[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins"
    )
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: List[str] = Field(default=["*"])
    cors_allow_headers: List[str] = Field(default=["*"])
    
    # Model Configuration
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="Sentence transformer model name"
    )
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    
    # API Limits
    max_content_length: int = Field(default=10000, description="Max characters in content")
    max_contexts_per_request: int = Field(default=20, description="Max contexts to return")
    max_tag_count: int = Field(default=20, description="Max tags per context")
    max_tag_length: int = Field(default=50, description="Max characters per tag")
    
    # Security
    enable_auth: bool = Field(default=False, description="Enable authentication")
    api_key: str = Field(default="", description="API key for authentication")
    
    class Config:
        env_file = ".env"
        env_prefix = "CONTEXTPILOT_"
        case_sensitive = False


# Global settings instance
settings = Settings()

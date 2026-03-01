"""
Configuration management for ContextPilot backend.
"""
import os
from typing import List, Optional
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
    log_format: str = Field(default="json", description="Log format (json or text)")

    # Monitoring
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics endpoint and instrumentation")
    
    # API Limits
    max_content_length: int = Field(default=10000, description="Max characters in content")
    max_contexts_per_request: int = Field(default=20, description="Max contexts to return")
    max_tag_count: int = Field(default=20, description="Max tags per context")
    max_tag_length: int = Field(default=50, description="Max characters per tag")
    
    # Security
    enable_auth: bool = Field(default=False, description="Enable authentication")
    api_key: str = Field(default="", description="API key for authentication")
    
    # Storage Configuration
    use_database: bool = Field(default=True, description="Use database storage (vs in-memory)")
    
    # Database Configuration
    database_url: str = Field(
        default="sqlite:///./contextpilot.db",
        description="Database connection URL"
    )
    database_echo: bool = Field(default=False, description="Echo SQL statements")
    
    # AI Integration
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_base_url: str = Field(default="", description="OpenAI base URL override")
    openai_default_model: str = Field(default="", description="OpenAI default model override")
    openai_temperature: Optional[float] = Field(default=None, description="OpenAI temperature override")
    openai_top_p: Optional[float] = Field(default=None, description="OpenAI top_p override")
    openai_max_tokens: Optional[int] = Field(default=None, description="OpenAI max tokens override")
    anthropic_api_key: str = Field(default="", description="Anthropic API key")
    anthropic_default_model: str = Field(default="", description="Anthropic default model override")
    anthropic_temperature: Optional[float] = Field(default=None, description="Anthropic temperature override")
    anthropic_top_p: Optional[float] = Field(default=None, description="Anthropic top_p override")
    anthropic_top_k: Optional[int] = Field(default=None, description="Anthropic top_k override")
    anthropic_max_tokens: Optional[int] = Field(default=None, description="Anthropic max tokens override")
    ollama_base_url: str = Field(default="http://localhost:11434", description="Ollama API endpoint")
    ollama_api_key: str = Field(default="ollama", description="Ollama API key (usually not required)")
    ollama_default_model: str = Field(default="", description="Ollama default model override")
    ollama_temperature: Optional[float] = Field(default=None, description="Ollama temperature override")
    ollama_top_p: Optional[float] = Field(default=None, description="Ollama top_p override")
    ollama_num_predict: Optional[int] = Field(default=None, description="Ollama num_predict override")
    ollama_num_ctx: Optional[int] = Field(default=None, description="Ollama num_ctx override")
    ollama_keep_alive: str = Field(default="", description="Ollama keep_alive override")
    default_ai_provider: str = Field(default="openai", description="Default AI provider (openai, anthropic, or ollama)")
    default_ai_model: str = Field(default="gpt-4o", description="Default AI model")
    ai_max_tokens: int = Field(default=2000, description="Max tokens for AI responses")
    ai_temperature: float = Field(default=0.7, description="AI temperature (0-2)")
    
    class Config:
        env_file = ".env"
        env_prefix = "CONTEXTPILOT_"
        case_sensitive = False


# Global settings instance
settings = Settings()

"""
Data models for ContextPilot.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
import uuid


class ContextType(str, Enum):
    """Types of context units."""
    PREFERENCE = "preference"
    DECISION = "decision"
    FACT = "fact"
    GOAL = "goal"


class ContextStatus(str, Enum):
    """Status of a context unit."""
    ACTIVE = "active"
    SUPERSEDED = "superseded"


class ContextUnit(BaseModel):
    """A single unit of user context."""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: ContextType
    content: str
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None
    source: str = "manual"
    tags: List[str] = Field(default_factory=list)
    status: ContextStatus = ContextStatus.ACTIVE
    superseded_by: Optional[str] = None  # ID of the context unit that replaces this one


class ContextUnitCreate(BaseModel):
    """Schema for creating a new context unit."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "preference",
                "content": "I prefer using React with TypeScript for frontend development",
                "confidence": 0.9,
                "tags": ["frontend", "react", "typescript"],
                "source": "manual"
            }
        }
    )
    
    type: ContextType
    content: str
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    tags: List[str] = Field(default_factory=list)
    source: str = "manual"


class ContextUnitUpdate(BaseModel):
    """Schema for updating a context unit."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "Updated preference: I prefer using Tailwind CSS",
                "confidence": 0.95,
                "tags": ["frontend", "css", "tailwind"]
            }
        }
    )
    
    type: Optional[ContextType] = None
    content: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    tags: Optional[List[str]] = None
    status: Optional[ContextStatus] = None
    superseded_by: Optional[str] = None


class TaskRequest(BaseModel):
    """Request to generate a contextualized prompt."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task": "Design a React component for user profile display",
                "max_context_units": 5
            }
        }
    )
    
    task: str
    max_context_units: int = Field(default=5, ge=1, le=20)


class RankedContextUnit(BaseModel):
    """Context unit with relevance score."""
    context_unit: ContextUnit
    relevance_score: float


class GeneratedPrompt(BaseModel):
    """Generated prompt with context."""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )
    
    original_task: str
    relevant_context: List[RankedContextUnit]
    generated_prompt: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AIRequest(BaseModel):
    """Request to generate an AI response."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task": "Write a Python function to calculate Fibonacci numbers",
                "max_context_units": 5,
                "provider": "openai",
                "model": "gpt-4-turbo-preview",
                "temperature": 0.7,
                "max_tokens": 2000,
                "use_compact": False,
                "conversation_id": None
            }
        }
    )
    
    task: str
    max_context_units: int = Field(default=5, ge=1, le=20)
    provider: Optional[str] = None  # "openai" or "anthropic"
    model: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=4000)
    use_compact: bool = False  # Use compact prompt format
    conversation_id: Optional[str] = None  # Continue existing conversation


class AIResponse(BaseModel):
    """AI-generated response with metadata."""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )
    
    conversation_id: str
    task: str
    response: str
    provider: str
    model: str
    context_ids: List[str]
    prompt_used: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SettingsResponse(BaseModel):
    """Current application settings."""
    openai_api_key_set: bool = Field(description="Whether OpenAI API key is configured")
    anthropic_api_key_set: bool = Field(description="Whether Anthropic API key is configured")
    default_ai_provider: str = Field(description="Default AI provider")
    default_ai_model: str = Field(description="Default AI model")
    ai_temperature: float = Field(description="AI temperature setting")
    ai_max_tokens: int = Field(description="AI max tokens setting")


class SettingsUpdate(BaseModel):
    """Settings update request."""
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key (optional)")
    anthropic_api_key: Optional[str] = Field(None, description="Anthropic API key (optional)")
    default_ai_provider: Optional[str] = Field(None, description="Default AI provider")
    default_ai_model: Optional[str] = Field(None, description="Default AI model")
    ai_temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="AI temperature")
    ai_max_tokens: Optional[int] = Field(None, ge=1, le=4000, description="AI max tokens")

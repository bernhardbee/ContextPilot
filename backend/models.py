"""
Data models for ContextPilot.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
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
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ContextUnitCreate(BaseModel):
    """Schema for creating a new context unit."""
    type: ContextType
    content: str
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    tags: List[str] = Field(default_factory=list)
    source: str = "manual"


class ContextUnitUpdate(BaseModel):
    """Schema for updating a context unit."""
    type: Optional[ContextType] = None
    content: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    tags: Optional[List[str]] = None
    status: Optional[ContextStatus] = None
    superseded_by: Optional[str] = None


class TaskRequest(BaseModel):
    """Request to generate a contextualized prompt."""
    task: str
    max_context_units: int = Field(default=5, ge=1, le=20)


class RankedContextUnit(BaseModel):
    """Context unit with relevance score."""
    context_unit: ContextUnit
    relevance_score: float


class GeneratedPrompt(BaseModel):
    """Generated prompt with context."""
    original_task: str
    relevant_context: List[RankedContextUnit]
    generated_prompt: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

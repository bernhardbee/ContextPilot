"""
SQLAlchemy database models for ContextPilot.
"""
from sqlalchemy import Column, String, Float, DateTime, Enum, ForeignKey, Text, Integer, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from database import Base
from models import ContextType, ContextStatus
from config import settings


# Check if we're using PostgreSQL for vector support
USE_PGVECTOR = "postgresql" in settings.database_url

if USE_PGVECTOR:
    from pgvector.sqlalchemy import Vector


class ContextUnitDB(Base):
    """Database model for context units."""
    __tablename__ = "context_units"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(Enum(ContextType), nullable=False)
    content = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False, default=1.0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    source = Column(String, nullable=False, default="manual")
    tags = Column(JSON, nullable=False, default=list)
    status = Column(Enum(ContextStatus), nullable=False, default=ContextStatus.ACTIVE)
    superseded_by = Column(String, ForeignKey("context_units.id"), nullable=True)
    
    # Vector embedding - use pgvector for PostgreSQL, JSON for SQLite
    if USE_PGVECTOR:
        embedding = Column(Vector(384), nullable=True)
    else:
        embedding = Column(JSON, nullable=True)
    
    # Relationships
    superseded_context = relationship(
        "ContextUnitDB",
        remote_side=[id],
        backref="supersedes"
    )
    
    def __repr__(self):
        return f"<ContextUnitDB(id={self.id}, type={self.type}, content={self.content[:50]}...)>"


class ConversationDB(Base):
    """Database model for AI conversations."""
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task = Column(Text, nullable=False)
    prompt_type = Column(String, nullable=False)  # "full" or "compact"
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    provider = Column(String, nullable=False)  # "openai" or "anthropic"
    model = Column(String, nullable=False)
    
    # Contexts used in this conversation
    context_ids = Column(JSON, nullable=False, default=list)
    
    # Relationships
    messages = relationship("MessageDB", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ConversationDB(id={self.id}, task={self.task[:50]}...)>"


class MessageDB(Base):
    """Database model for messages in conversations."""
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False)  # "system", "user", "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Metadata
    tokens = Column(Integer, nullable=True)
    finish_reason = Column(String, nullable=True)
    model = Column(String, nullable=True)  # Track which AI model generated this message
    
    # Relationships
    conversation = relationship("ConversationDB", back_populates="messages")
    
    def __repr__(self):
        return f"<MessageDB(id={self.id}, role={self.role}, content={self.content[:50]}...)>"

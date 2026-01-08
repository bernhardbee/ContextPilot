"""
Database-backed storage for context units.
"""
from typing import List, Optional, Dict, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
import numpy as np

from db_models import ContextUnitDB
from models import ContextUnit, ContextStatus
from storage_interface import ContextStoreInterface
from database import get_db_session
from logger import logger


class DatabaseContextStore(ContextStoreInterface):
    """
    Database-backed storage for context units with vector embeddings.
    """
    
    def __init__(self):
        """Initialize the database context store."""
        logger.info("Initialized DatabaseContextStore")
    
    def add(self, context: ContextUnit, embedding: Optional[np.ndarray] = None):
        """
        Add a new context unit to the database.
        
        Args:
            context: The context unit to add
            embedding: Optional vector embedding
        """
        with get_db_session() as db:
            db_context = ContextUnitDB(
                id=context.id,
                type=context.type,
                content=context.content,
                confidence=context.confidence,
                created_at=context.created_at,
                last_used=context.last_used,
                source=context.source,
                tags=context.tags,
                status=context.status,
                superseded_by=context.superseded_by,
                embedding=embedding.tolist() if embedding is not None else None
            )
            db.add(db_context)
            # Commit handled by context manager
            logger.debug(f"Added context {context.id} to database")
    
    def get(self, context_id: str) -> Optional[ContextUnit]:
        """
        Retrieve a context unit by ID.
        
        Args:
            context_id: The ID of the context to retrieve
            
        Returns:
            The context unit or None if not found
        """
        with get_db_session() as db:
            db_context = db.query(ContextUnitDB).filter(ContextUnitDB.id == context_id).first()
            if db_context:
                return self._to_context_unit(db_context)
            return None
    
    def list_all(self, include_superseded: bool = False) -> List[ContextUnit]:
        """
        List all context units.
        
        Args:
            include_superseded: Whether to include superseded contexts
            
        Returns:
            List of context units
        """
        with get_db_session() as db:
            query = db.query(ContextUnitDB)
            if not include_superseded:
                query = query.filter(ContextUnitDB.status == ContextStatus.ACTIVE)
            db_contexts = query.all()
            return [self._to_context_unit(ctx) for ctx in db_contexts]
    
    def update(self, context_id: str, updates: Dict) -> Optional[ContextUnit]:
        """
        Update a context unit.
        
        Args:
            context_id: The ID of the context to update
            updates: Dictionary of fields to update
            
        Returns:
            The updated context unit or None if not found
        """
        with get_db_session() as db:
            db_context = db.query(ContextUnitDB).filter(ContextUnitDB.id == context_id).first()
            if not db_context:
                return None
            
            for key, value in updates.items():
                if hasattr(db_context, key):
                    setattr(db_context, key, value)
            
            # Commit and refresh handled by context manager
            logger.debug(f"Updated context {context_id}")
            return self._to_context_unit(db_context)
    
    def delete(self, context_id: str) -> bool:
        """
        Delete a context unit.
        
        Args:
            context_id: The ID of the context to delete
            
        Returns:
            True if deleted, False if not found
        """
        with get_db_session() as db:
            db_context = db.query(ContextUnitDB).filter(ContextUnitDB.id == context_id).first()
            if not db_context:
                return False
            
            db.delete(db_context)
            # Commit handled by context manager
            logger.debug(f"Deleted context {context_id}")
            return True
    
    def supersede(self, old_id: str, new_id: str) -> bool:
        """
        Mark a context as superseded by another.
        
        Args:
            old_id: The ID of the context being superseded
            new_id: The ID of the new context
            
        Returns:
            True if successful, False if old context not found
        """
        with get_db_session() as db:
            old_context = db.query(ContextUnitDB).filter(ContextUnitDB.id == old_id).first()
            if not old_context:
                return False
            
            old_context.status = ContextStatus.SUPERSEDED
            old_context.superseded_by = new_id
            # Commit handled by context manager
            logger.debug(f"Context {old_id} superseded by {new_id}")
            return True
    
    def get_embedding(self, context_id: str) -> Optional[np.ndarray]:
        """
        Get the embedding vector for a context.
        
        Args:
            context_id: The ID of the context
            
        Returns:
            The embedding vector or None if not found
        """
        with get_db_session() as db:
            db_context = db.query(ContextUnitDB).filter(ContextUnitDB.id == context_id).first()
            if db_context and db_context.embedding:
                return np.array(db_context.embedding)
            return None
    
    def update_embedding(self, context_id: str, embedding: np.ndarray):
        """
        Update the embedding vector for a context.
        
        Args:
            context_id: The ID of the context
            embedding: The new embedding vector
        """
        with get_db_session() as db:
            db_context = db.query(ContextUnitDB).filter(ContextUnitDB.id == context_id).first()
            if db_context:
                db_context.embedding = embedding.tolist()
                # Commit handled by context manager
                logger.debug(f"Updated embedding for context {context_id}")
    
    def list_with_embeddings(self, include_superseded: bool = False) -> List[tuple]:
        """
        List all contexts with their embeddings.
        
        Args:
            include_superseded: Whether to include superseded contexts
            
        Returns:
            List of (ContextUnit, embedding) tuples
        """
        with get_db_session() as db:
            query = db.query(ContextUnitDB)
            if not include_superseded:
                query = query.filter(ContextUnitDB.status == ContextStatus.ACTIVE)
            
            result = []
            for db_context in query.all():
                context = self._to_context_unit(db_context)
                embedding = np.array(db_context.embedding) if db_context.embedding else None
                result.append((context, embedding))
            
            return result
    
    def _to_context_unit(self, db_context: ContextUnitDB) -> ContextUnit:
        """Convert database model to ContextUnit."""
        return ContextUnit(
            id=db_context.id,
            type=db_context.type,
            content=db_context.content,
            confidence=db_context.confidence,
            created_at=db_context.created_at,
            last_used=db_context.last_used,
            source=db_context.source,
            tags=db_context.tags,
            status=db_context.status,
            superseded_by=db_context.superseded_by
        )


# Global database context store instance
db_context_store = DatabaseContextStore()

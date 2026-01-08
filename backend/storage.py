"""
In-memory storage for context units with vector embeddings.
"""
from typing import List, Optional, Dict, Tuple
from datetime import datetime
from models import ContextUnit, ContextType, ContextStatus
from storage_interface import ContextStoreInterface
import numpy as np
from logger import logger


class ContextStore(ContextStoreInterface):
    """In-memory store for context units with vector embeddings."""
    
    def __init__(self):
        self._contexts: Dict[str, ContextUnit] = {}
        self._embeddings: Dict[str, np.ndarray] = {}
        logger.info("ContextStore initialized")
    
    def add(self, context: ContextUnit, embedding: Optional[np.ndarray] = None):
        """Add a context unit to the store."""
        self._contexts[context.id] = context
        if embedding is not None:
            self._embeddings[context.id] = embedding
        logger.debug(f"Added context unit {context.id} of type {context.type}")
    
    def get(self, context_id: str) -> Optional[ContextUnit]:
        """Get a context unit by ID."""
        return self._contexts.get(context_id)
    
    def list_all(self, include_superseded: bool = False) -> List[ContextUnit]:
        """List all context units."""
        if include_superseded:
            return list(self._contexts.values())
        return [c for c in self._contexts.values() if c.status == ContextStatus.ACTIVE]
    
    def update(self, context_id: str, updates: dict) -> Optional[ContextUnit]:
        """Update a context unit."""
        context = self._contexts.get(context_id)
        if not context:
            return None
        
        for key, value in updates.items():
            if value is not None and hasattr(context, key):
                setattr(context, key, value)
        
        return context
    
    def delete(self, context_id: str) -> bool:
        """Delete a context unit."""
        if context_id in self._contexts:
            del self._contexts[context_id]
            if context_id in self._embeddings:
                del self._embeddings[context_id]
            logger.debug(f"Deleted context unit {context_id}")
            return True
        logger.warning(f"Attempted to delete non-existent context {context_id}")
        return False
    
    def get_embedding(self, context_id: str) -> Optional[np.ndarray]:
        """Get the embedding for a context unit."""
        return self._embeddings.get(context_id)
    
    def update_embedding(self, context_id: str, embedding: np.ndarray) -> bool:
        """
        Update the embedding for a context unit.
        
        Args:
            context_id: ID of the context unit
            embedding: New embedding vector
            
        Returns:
            True if updated, False if context not found
        """
        if context_id not in self._contexts:
            return False
        self._embeddings[context_id] = embedding
        logger.debug(f"Updated embedding for context {context_id}")
        return True
    
    def list_with_embeddings(self) -> List[tuple[ContextUnit, np.ndarray]]:
        """List all active context units with their embeddings."""
        result = []
        for context in self._contexts.values():
            if context.status == ContextStatus.ACTIVE and context.id in self._embeddings:
                result.append((context, self._embeddings[context.id]))
        return result
    
    def supersede(self, old_id: str, new_context: ContextUnit) -> bool:
        """Mark an old context as superseded by a new one."""
        old_context = self._contexts.get(old_id)
        if not old_context:
            return False
        
        old_context.status = ContextStatus.SUPERSEDED
        old_context.superseded_by = new_context.id
        self._contexts[new_context.id] = new_context
        
        return True


# Global instance
context_store = ContextStore()

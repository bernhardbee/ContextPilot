"""
Abstract base class for context storage implementations.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
import numpy as np

from models import ContextUnit


class ContextStoreInterface(ABC):
    """
    Abstract interface for context storage implementations.
    
    This interface defines the contract that all storage implementations
    (in-memory, database, etc.) must follow.
    """
    
    @abstractmethod
    def add(self, context: ContextUnit, embedding: Optional[np.ndarray] = None) -> None:
        """
        Add a context unit to the store.
        
        Args:
            context: The context unit to add
            embedding: Optional vector embedding for the context
        """
        pass
    
    @abstractmethod
    def get(self, context_id: str) -> Optional[ContextUnit]:
        """
        Retrieve a context unit by ID.
        
        Args:
            context_id: The ID of the context to retrieve
            
        Returns:
            The context unit or None if not found
        """
        pass
    
    @abstractmethod
    def list_all(self, include_superseded: bool = False) -> List[ContextUnit]:
        """
        List all context units.
        
        Args:
            include_superseded: Whether to include superseded contexts
            
        Returns:
            List of context units
        """
        pass
    
    @abstractmethod
    def update(self, context_id: str, updates: dict) -> Optional[ContextUnit]:
        """
        Update a context unit.
        
        Args:
            context_id: ID of the context to update
            updates: Dictionary of fields to update
            
        Returns:
            Updated context unit or None if not found
        """
        pass
    
    @abstractmethod
    def delete(self, context_id: str) -> bool:
        """
        Delete a context unit.
        
        Args:
            context_id: ID of the context to delete
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    def supersede(self, old_context_id: str, new_context: ContextUnit, 
                  embedding: Optional[np.ndarray] = None) -> bool:
        """
        Mark a context as superseded by a new one.
        
        Args:
            old_context_id: ID of the context to supersede
            new_context: The new context that replaces it
            embedding: Optional embedding for the new context
            
        Returns:
            True if successful, False if old context not found
        """
        pass
    
    @abstractmethod
    def get_embedding(self, context_id: str) -> Optional[np.ndarray]:
        """
        Get the embedding for a context unit.
        
        Args:
            context_id: ID of the context
            
        Returns:
            Embedding vector or None if not found
        """
        pass
    
    @abstractmethod
    def update_embedding(self, context_id: str, embedding: np.ndarray) -> bool:
        """
        Update the embedding for a context unit.
        
        Args:
            context_id: ID of the context
            embedding: New embedding vector
            
        Returns:
            True if updated, False if context not found
        """
        pass
    
    @abstractmethod
    def list_with_embeddings(self) -> List[Tuple[ContextUnit, np.ndarray]]:
        """
        List all active contexts that have embeddings.
        
        Returns:
            List of tuples (context, embedding)
        """
        pass

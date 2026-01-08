"""
Dependency injection for ContextPilot.
Provides centralized management of service instances.
"""
from typing import Optional
from functools import lru_cache

from config import settings
from logger import logger
from relevance import RelevanceEngine
from composer import PromptComposer
from ai_service import AIService
from storage_interface import ContextStoreInterface

# Import database storage if enabled
if settings.use_database:
    from db_storage import DatabaseContextStore


class ServiceContainer:
    """
    Container for managing application services and dependencies.
    Implements lazy initialization and singleton pattern.
    """
    
    def __init__(self):
        """Initialize the service container."""
        self._context_store: Optional[ContextStoreInterface] = None
        self._relevance_engine: Optional[RelevanceEngine] = None
        self._prompt_composer: Optional[PromptComposer] = None
        self._ai_service: Optional[AIService] = None
    
    def get_context_store(self) -> ContextStoreInterface:
        """
        Get or create the context store instance.
        
        Returns:
            ContextStore instance (database or in-memory based on config)
        """
        if self._context_store is None:
            if settings.use_database:
                from db_storage import db_context_store
                self._context_store = db_context_store
                logger.info("Initialized database context store")
            else:
                from storage import context_store
                self._context_store = context_store
                logger.info("Initialized in-memory context store")
        
        return self._context_store
    
    def get_relevance_engine(self) -> RelevanceEngine:
        """
        Get or create the relevance engine instance.
        
        Returns:
            RelevanceEngine instance
            
        Raises:
            RuntimeError: If model fails to load
        """
        if self._relevance_engine is None:
            self._relevance_engine = RelevanceEngine(
                model_name=settings.embedding_model
            )
            logger.info(f"Initialized relevance engine with model: {settings.embedding_model}")
        
        return self._relevance_engine
    
    def get_prompt_composer(self) -> PromptComposer:
        """
        Get or create the prompt composer instance.
        
        Returns:
            PromptComposer instance
        """
        if self._prompt_composer is None:
            self._prompt_composer = PromptComposer()
            logger.info("Initialized prompt composer")
        
        return self._prompt_composer
    
    def get_ai_service(self) -> AIService:
        """
        Get or create the AI service instance.
        
        Returns:
            AIService instance
        """
        if self._ai_service is None:
            self._ai_service = AIService()
            logger.info("Initialized AI service")
        
        return self._ai_service
    
    def reset(self) -> None:
        """
        Reset all services (useful for testing).
        """
        self._context_store = None
        self._relevance_engine = None
        self._prompt_composer = None
        self._ai_service = None
        logger.info("Reset service container")


# Global service container instance
_container: Optional[ServiceContainer] = None


def get_container() -> ServiceContainer:
    """
    Get the global service container.
    
    Returns:
        ServiceContainer instance
    """
    global _container
    if _container is None:
        _container = ServiceContainer()
    return _container


# Dependency functions for FastAPI
def get_context_store() -> ContextStoreInterface:
    """
    Dependency for injecting context store.
    
    Returns:
        ContextStore instance
    """
    return get_container().get_context_store()


def get_relevance_engine() -> RelevanceEngine:
    """
    Dependency for injecting relevance engine.
    
    Returns:
        RelevanceEngine instance
    """
    return get_container().get_relevance_engine()


def get_prompt_composer() -> PromptComposer:
    """
    Dependency for injecting prompt composer.
    
    Returns:
        PromptComposer instance
    """
    return get_container().get_prompt_composer()


def get_ai_service() -> AIService:
    """
    Dependency for injecting AI service.
    
    Returns:
        AIService instance
    """
    return get_container().get_ai_service()

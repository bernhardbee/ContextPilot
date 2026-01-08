"""
Test cases for the dependency injection container.
"""
import pytest
from dependencies import ServiceContainer, get_container
from relevance import RelevanceEngine
from composer import PromptComposer
from ai_service import AIService
from storage_interface import ContextStoreInterface


def test_service_container_initialization():
    """Test that service container initializes correctly."""
    container = ServiceContainer()
    assert container is not None
    assert container._context_store is None
    assert container._relevance_engine is None
    assert container._prompt_composer is None
    assert container._ai_service is None


def test_get_context_store():
    """Test getting context store from container."""
    container = ServiceContainer()
    store = container.get_context_store()
    assert store is not None
    assert isinstance(store, ContextStoreInterface)
    
    # Should return same instance on second call
    store2 = container.get_context_store()
    assert store is store2


def test_get_relevance_engine():
    """Test getting relevance engine from container."""
    container = ServiceContainer()
    engine = container.get_relevance_engine()
    assert engine is not None
    assert isinstance(engine, RelevanceEngine)
    
    # Should return same instance on second call
    engine2 = container.get_relevance_engine()
    assert engine is engine2


def test_get_prompt_composer():
    """Test getting prompt composer from container."""
    container = ServiceContainer()
    composer = container.get_prompt_composer()
    assert composer is not None
    assert isinstance(composer, PromptComposer)
    
    # Should return same instance on second call
    composer2 = container.get_prompt_composer()
    assert composer is composer2


def test_get_ai_service():
    """Test getting AI service from container."""
    container = ServiceContainer()
    service = container.get_ai_service()
    assert service is not None
    assert isinstance(service, AIService)
    
    # Should return same instance on second call
    service2 = container.get_ai_service()
    assert service is service2


def test_container_reset():
    """Test resetting container clears all services."""
    container = ServiceContainer()
    
    # Initialize all services
    container.get_context_store()
    container.get_relevance_engine()
    container.get_prompt_composer()
    container.get_ai_service()
    
    assert container._context_store is not None
    assert container._relevance_engine is not None
    assert container._prompt_composer is not None
    assert container._ai_service is not None
    
    # Reset
    container.reset()
    
    assert container._context_store is None
    assert container._relevance_engine is None
    assert container._prompt_composer is None
    assert container._ai_service is None


def test_global_container():
    """Test that get_container returns a global instance."""
    container1 = get_container()
    container2 = get_container()
    assert container1 is container2


def test_dependency_functions():
    """Test that dependency functions work correctly."""
    from dependencies import (
        get_context_store,
        get_relevance_engine,
        get_prompt_composer,
        get_ai_service
    )
    
    store = get_context_store()
    engine = get_relevance_engine()
    composer = get_prompt_composer()
    service = get_ai_service()
    
    assert isinstance(store, ContextStoreInterface)
    assert isinstance(engine, RelevanceEngine)
    assert isinstance(composer, PromptComposer)
    assert isinstance(service, AIService)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

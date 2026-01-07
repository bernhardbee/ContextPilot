"""
Unit tests for ContextPilot backend (without model loading).
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from models import (
    ContextUnit, ContextUnitCreate, ContextUnitUpdate,
    ContextType, ContextStatus, TaskRequest, RankedContextUnit
)
from storage import ContextStore


class TestModels:
    """Test Pydantic models."""
    
    def test_context_unit_creation(self):
        """Test creating a ContextUnit."""
        context = ContextUnit(
            type=ContextType.PREFERENCE,
            content="Test content",
            confidence=0.9,
            tags=["test"]
        )
        assert context.type == ContextType.PREFERENCE
        assert context.content == "Test content"
        assert context.confidence == 0.9
        assert context.tags == ["test"]
        assert context.status == ContextStatus.ACTIVE
        assert context.id is not None
    
    def test_context_unit_defaults(self):
        """Test ContextUnit default values."""
        context = ContextUnit(
            type=ContextType.FACT,
            content="Test fact"
        )
        assert context.confidence == 1.0
        assert context.tags == []
        assert context.source == "manual"
        assert context.status == ContextStatus.ACTIVE
    
    def test_context_unit_validation_confidence_min(self):
        """Test confidence minimum validation."""
        with pytest.raises(Exception):
            ContextUnit(
                type=ContextType.FACT,
                content="Test",
                confidence=-0.1
            )
    
    def test_context_unit_validation_confidence_max(self):
        """Test confidence maximum validation."""
        with pytest.raises(Exception):
            ContextUnit(
                type=ContextType.FACT,
                content="Test",
                confidence=1.5
            )
    
    def test_context_unit_create_schema(self):
        """Test ContextUnitCreate schema."""
        create_data = ContextUnitCreate(
            type=ContextType.GOAL,
            content="Test goal",
            confidence=0.85,
            tags=["goal", "test"]
        )
        assert create_data.type == ContextType.GOAL
        assert create_data.content == "Test goal"
        assert create_data.confidence == 0.85
        assert create_data.tags == ["goal", "test"]
    
    def test_context_unit_update_schema(self):
        """Test ContextUnitUpdate schema."""
        update_data = ContextUnitUpdate(
            content="Updated content",
            confidence=0.95
        )
        assert update_data.content == "Updated content"
        assert update_data.confidence == 0.95
        assert update_data.type is None  # Not updated
    
    def test_task_request_schema(self):
        """Test TaskRequest schema."""
        task = TaskRequest(
            task="Test task",
            max_context_units=10
        )
        assert task.task == "Test task"
        assert task.max_context_units == 10
    
    def test_task_request_defaults(self):
        """Test TaskRequest default values."""
        task = TaskRequest(task="Test task")
        assert task.max_context_units == 5


class TestStorage:
    """Test ContextStore."""
    
    def setup_method(self):
        """Setup for each test."""
        self.store = ContextStore()
    
    def test_add_context_without_embedding(self):
        """Test adding a context without embedding."""
        context = ContextUnit(
            type=ContextType.PREFERENCE,
            content="Test preference"
        )
        
        self.store.add(context)
        
        retrieved = self.store.get(context.id)
        assert retrieved is not None
        assert retrieved.content == "Test preference"
        assert retrieved.id == context.id
    
    def test_add_context_with_embedding(self):
        """Test adding a context with embedding."""
        context = ContextUnit(
            type=ContextType.PREFERENCE,
            content="Test preference"
        )
        embedding = np.random.rand(384)
        
        self.store.add(context, embedding)
        
        retrieved = self.store.get(context.id)
        assert retrieved is not None
        
        retrieved_emb = self.store.get_embedding(context.id)
        assert retrieved_emb is not None
        assert np.array_equal(retrieved_emb, embedding)
    
    def test_list_contexts_empty(self):
        """Test listing contexts when store is empty."""
        contexts = self.store.list_all()
        assert contexts == []
    
    def test_list_contexts_multiple(self):
        """Test listing multiple contexts."""
        context1 = ContextUnit(type=ContextType.FACT, content="Fact 1")
        context2 = ContextUnit(type=ContextType.GOAL, content="Goal 1")
        context3 = ContextUnit(type=ContextType.DECISION, content="Decision 1")
        
        self.store.add(context1)
        self.store.add(context2)
        self.store.add(context3)
        
        contexts = self.store.list_all()
        assert len(contexts) == 3
    
    def test_list_contexts_exclude_superseded(self):
        """Test that superseded contexts are excluded by default."""
        context1 = ContextUnit(type=ContextType.FACT, content="Active")
        context2 = ContextUnit(type=ContextType.FACT, content="Superseded")
        context2.status = ContextStatus.SUPERSEDED
        
        self.store.add(context1)
        self.store.add(context2)
        
        contexts = self.store.list_all(include_superseded=False)
        assert len(contexts) == 1
        assert contexts[0].content == "Active"
    
    def test_list_contexts_include_superseded(self):
        """Test listing all contexts including superseded."""
        context1 = ContextUnit(type=ContextType.FACT, content="Active")
        context2 = ContextUnit(type=ContextType.FACT, content="Superseded")
        context2.status = ContextStatus.SUPERSEDED
        
        self.store.add(context1)
        self.store.add(context2)
        
        contexts = self.store.list_all(include_superseded=True)
        assert len(contexts) == 2
    
    def test_update_context(self):
        """Test updating a context."""
        context = ContextUnit(
            type=ContextType.DECISION,
            content="Original content",
            confidence=0.5
        )
        self.store.add(context)
        
        updates = {"content": "Updated content", "confidence": 0.7}
        updated = self.store.update(context.id, updates)
        
        assert updated is not None
        assert updated.content == "Updated content"
        assert updated.confidence == 0.7
        assert updated.type == ContextType.DECISION  # Unchanged
    
    def test_update_nonexistent_context(self):
        """Test updating a context that doesn't exist."""
        updates = {"content": "Updated"}
        updated = self.store.update("nonexistent-id", updates)
        assert updated is None
    
    def test_delete_context(self):
        """Test deleting a context."""
        context = ContextUnit(type=ContextType.FACT, content="To delete")
        self.store.add(context)
        
        success = self.store.delete(context.id)
        assert success is True
        
        retrieved = self.store.get(context.id)
        assert retrieved is None
    
    def test_delete_nonexistent_context(self):
        """Test deleting a context that doesn't exist."""
        success = self.store.delete("nonexistent-id")
        assert success is False
    
    def test_delete_context_with_embedding(self):
        """Test deleting a context also removes its embedding."""
        context = ContextUnit(type=ContextType.FACT, content="To delete")
        embedding = np.random.rand(384)
        
        self.store.add(context, embedding)
        self.store.delete(context.id)
        
        retrieved_emb = self.store.get_embedding(context.id)
        assert retrieved_emb is None
    
    def test_supersede_context(self):
        """Test superseding a context."""
        old_context = ContextUnit(
            type=ContextType.PREFERENCE,
            content="Old preference"
        )
        new_context = ContextUnit(
            type=ContextType.PREFERENCE,
            content="New preference"
        )
        
        self.store.add(old_context)
        success = self.store.supersede(old_context.id, new_context)
        
        assert success is True
        
        old = self.store.get(old_context.id)
        assert old.status == ContextStatus.SUPERSEDED
        assert old.superseded_by == new_context.id
        
        new = self.store.get(new_context.id)
        assert new is not None
        assert new.status == ContextStatus.ACTIVE
    
    def test_supersede_nonexistent_context(self):
        """Test superseding a context that doesn't exist."""
        new_context = ContextUnit(
            type=ContextType.PREFERENCE,
            content="New"
        )
        success = self.store.supersede("nonexistent-id", new_context)
        assert success is False
    
    def test_list_with_embeddings(self):
        """Test listing contexts with embeddings."""
        context1 = ContextUnit(type=ContextType.FACT, content="With embedding")
        context2 = ContextUnit(type=ContextType.FACT, content="Without embedding")
        
        emb1 = np.random.rand(384)
        self.store.add(context1, emb1)
        self.store.add(context2)
        
        contexts_with_emb = self.store.list_with_embeddings()
        
        assert len(contexts_with_emb) == 1
        assert contexts_with_emb[0][0].id == context1.id
        assert np.array_equal(contexts_with_emb[0][1], emb1)


class TestComposer:
    """Test PromptComposer (mocked to avoid model loading)."""
    
    def test_compose_empty(self):
        """Test composing with no context."""
        # Import composer module
        from composer import PromptComposer
        
        composer = PromptComposer()
        task = "Write a function"
        result = composer.compose(task, [])
        
        assert result.original_task == task
        assert result.relevant_context == []
        assert result.generated_prompt == task
    
    def test_compose_with_single_context(self):
        """Test composing with one context."""
        from composer import PromptComposer
        
        composer = PromptComposer()
        context = ContextUnit(
            type=ContextType.PREFERENCE,
            content="I prefer concise code",
            confidence=0.9,
            tags=["style"]
        )
        
        ranked = RankedContextUnit(
            context_unit=context,
            relevance_score=0.85
        )
        
        task = "Write a function"
        result = composer.compose(task, [ranked])
        
        assert result.original_task == task
        assert len(result.relevant_context) == 1
        assert "Context" in result.generated_prompt
        assert "Preference" in result.generated_prompt
        assert "concise code" in result.generated_prompt
        assert task in result.generated_prompt
    
    def test_compose_with_multiple_contexts(self):
        """Test composing with multiple contexts."""
        from composer import PromptComposer
        
        composer = PromptComposer()
        contexts = [
            RankedContextUnit(
                context_unit=ContextUnit(
                    type=ContextType.PREFERENCE,
                    content="I prefer Python",
                    confidence=0.9
                ),
                relevance_score=0.85
            ),
            RankedContextUnit(
                context_unit=ContextUnit(
                    type=ContextType.DECISION,
                    content="Using FastAPI",
                    confidence=0.95
                ),
                relevance_score=0.80
            )
        ]
        
        result = composer.compose("Build an API", contexts)
        
        assert "Preference" in result.generated_prompt
        assert "Decision" in result.generated_prompt
        assert "Python" in result.generated_prompt
        assert "FastAPI" in result.generated_prompt


def test_imports():
    """Test that all modules can be imported."""
    import models
    import storage
    import composer
    # Note: relevance and main require model download
    assert models is not None
    assert storage is not None
    assert composer is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

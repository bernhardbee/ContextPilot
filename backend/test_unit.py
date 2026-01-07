"""
Unit tests for ContextPilot backend.
"""
import pytest
from datetime import datetime
from models import (
    ContextUnit, ContextUnitCreate, ContextUnitUpdate,
    ContextType, ContextStatus, TaskRequest, RankedContextUnit
)
from storage import ContextStore
from relevance import RelevanceEngine
from composer import PromptComposer
import numpy as np


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
    
    def test_context_unit_validation(self):
        """Test ContextUnit validation."""
        # Valid confidence
        context = ContextUnit(
            type=ContextType.FACT,
            content="Test",
            confidence=0.5
        )
        assert context.confidence == 0.5
        
        # Invalid confidence should fail
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


class TestStorage:
    """Test ContextStore."""
    
    def setup_method(self):
        """Setup for each test."""
        self.store = ContextStore()
    
    def test_add_context(self):
        """Test adding a context."""
        context = ContextUnit(
            type=ContextType.PREFERENCE,
            content="Test preference"
        )
        embedding = np.random.rand(384)
        
        self.store.add(context, embedding)
        
        retrieved = self.store.get(context.id)
        assert retrieved is not None
        assert retrieved.content == "Test preference"
    
    def test_list_contexts(self):
        """Test listing contexts."""
        context1 = ContextUnit(type=ContextType.FACT, content="Fact 1")
        context2 = ContextUnit(type=ContextType.GOAL, content="Goal 1")
        
        self.store.add(context1)
        self.store.add(context2)
        
        contexts = self.store.list_all()
        assert len(contexts) == 2
    
    def test_update_context(self):
        """Test updating a context."""
        context = ContextUnit(
            type=ContextType.DECISION,
            content="Original content"
        )
        self.store.add(context)
        
        updates = {"content": "Updated content", "confidence": 0.7}
        updated = self.store.update(context.id, updates)
        
        assert updated is not None
        assert updated.content == "Updated content"
        assert updated.confidence == 0.7
    
    def test_delete_context(self):
        """Test deleting a context."""
        context = ContextUnit(type=ContextType.FACT, content="To delete")
        self.store.add(context)
        
        success = self.store.delete(context.id)
        assert success is True
        
        retrieved = self.store.get(context.id)
        assert retrieved is None
    
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


class TestRelevanceEngine:
    """Test RelevanceEngine."""
    
    def setup_method(self):
        """Setup for each test."""
        self.engine = RelevanceEngine()
        self.store = ContextStore()
    
    def test_encode(self):
        """Test encoding text to embeddings."""
        text = "This is a test"
        embedding = self.engine.encode(text)
        
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape[0] == 384  # Model dimension
    
    def test_compute_similarity(self):
        """Test computing similarity between embeddings."""
        emb1 = self.engine.encode("Python programming")
        emb2 = self.engine.encode("Python coding")
        emb3 = self.engine.encode("cooking recipes")
        
        sim_similar = self.engine.compute_similarity(emb1, emb2)
        sim_different = self.engine.compute_similarity(emb1, emb3)
        
        # Similar texts should have higher similarity
        assert sim_similar > sim_different
        assert 0 <= sim_similar <= 1
        assert 0 <= sim_different <= 1
    
    def test_rank_contexts(self):
        """Test ranking contexts by relevance."""
        # Add test contexts
        context1 = ContextUnit(
            type=ContextType.PREFERENCE,
            content="I prefer Python for data processing",
            confidence=0.9,
            tags=["python", "data"]
        )
        context2 = ContextUnit(
            type=ContextType.FACT,
            content="I work with JavaScript frameworks",
            confidence=0.8,
            tags=["javascript"]
        )
        
        emb1 = self.engine.encode(context1.content)
        emb2 = self.engine.encode(context2.content)
        
        self.store.add(context1, emb1)
        self.store.add(context2, emb2)
        
        # Task related to Python
        task = "Write a Python function for data processing"
        ranked = self.engine.rank_contexts(task, self.store, max_results=2)
        
        assert len(ranked) <= 2
        assert all(isinstance(r, RankedContextUnit) for r in ranked)
        
        # First result should be Python-related
        if len(ranked) > 0:
            assert ranked[0].context_unit.id == context1.id


class TestPromptComposer:
    """Test PromptComposer."""
    
    def setup_method(self):
        """Setup for each test."""
        self.composer = PromptComposer()
    
    def test_compose_empty(self):
        """Test composing with no context."""
        task = "Write a function"
        result = self.composer.compose(task, [])
        
        assert result.original_task == task
        assert result.relevant_context == []
        assert result.generated_prompt == task
    
    def test_compose_with_context(self):
        """Test composing with context."""
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
        result = self.composer.compose(task, [ranked])
        
        assert result.original_task == task
        assert len(result.relevant_context) == 1
        assert "Context" in result.generated_prompt
        assert "Preference" in result.generated_prompt
        assert "concise code" in result.generated_prompt
        assert task in result.generated_prompt
    
    def test_compose_compact(self):
        """Test compact composition."""
        context = ContextUnit(
            type=ContextType.GOAL,
            content="Build an MVP quickly",
            confidence=1.0
        )
        
        ranked = RankedContextUnit(
            context_unit=context,
            relevance_score=0.9
        )
        
        task = "Design a feature"
        result = self.composer.compose_compact(task, [ranked])
        
        assert result.original_task == task
        assert "Build an MVP quickly" in result.generated_prompt
        assert task in result.generated_prompt


class TestIntegration:
    """Integration tests."""
    
    def setup_method(self):
        """Setup for each test."""
        self.store = ContextStore()
        self.engine = RelevanceEngine()
        self.composer = PromptComposer()
    
    def test_full_workflow(self):
        """Test complete workflow from context to prompt."""
        # Step 1: Create and store contexts
        contexts = [
            ContextUnit(
                type=ContextType.PREFERENCE,
                content="I prefer Python for backend",
                confidence=0.95,
                tags=["python", "backend"]
            ),
            ContextUnit(
                type=ContextType.DECISION,
                content="Using FastAPI for APIs",
                confidence=0.9,
                tags=["fastapi", "api"]
            ),
            ContextUnit(
                type=ContextType.GOAL,
                content="Build scalable services",
                confidence=0.85,
                tags=["scalability"]
            )
        ]
        
        for context in contexts:
            embedding = self.engine.encode(context.content)
            self.store.add(context, embedding)
        
        # Step 2: Rank contexts for a task
        task = "Create a new API endpoint"
        ranked = self.engine.rank_with_keywords(
            task, self.store, max_results=3
        )
        
        assert len(ranked) > 0
        assert all(isinstance(r, RankedContextUnit) for r in ranked)
        
        # Step 3: Compose prompt
        prompt = self.composer.compose(task, ranked)
        
        assert prompt.original_task == task
        assert len(prompt.relevant_context) > 0
        assert "Context" in prompt.generated_prompt
        assert task in prompt.generated_prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

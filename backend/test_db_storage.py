"""
Tests for database storage functionality.
"""
import pytest
from datetime import datetime
import numpy as np
import tempfile
import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db_storage import DatabaseContextStore
from models import ContextUnit, ContextType, ContextStatus
from database import Base
import database
import db_storage


@pytest.fixture(scope="function")
def db_store(monkeypatch):
    """Create a fresh database for each test using a temporary file."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_file.close()
    test_db_url = f"sqlite:///{temp_file.name}"
    test_engine = create_engine(test_db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    Base.metadata.create_all(bind=test_engine)

    @contextmanager
    def test_db_session():
        db = SessionLocal()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    monkeypatch.setattr(database, "engine", test_engine)
    monkeypatch.setattr(database, "SessionLocal", SessionLocal)
    monkeypatch.setattr(database, "get_db_session", test_db_session)
    monkeypatch.setattr(db_storage, "get_db_session", test_db_session)

    store = DatabaseContextStore()
    yield store

    test_engine.dispose()
    os.unlink(temp_file.name)


class TestDatabaseContextStore:
    """Tests for DatabaseContextStore."""
    
    def test_add_and_get_context(self, db_store):
        """Test adding and retrieving a context."""
        context = ContextUnit(
            type=ContextType.PREFERENCE,
            content="I prefer Python over JavaScript",
            confidence=0.9,
            tags=["language", "preference"]
        )
        
        db_store.add(context)
        retrieved = db_store.get(context.id)
        
        assert retrieved is not None
        assert retrieved.id == context.id
        assert retrieved.content == context.content
        assert retrieved.type == ContextType.PREFERENCE
        assert retrieved.confidence == 0.9
        assert retrieved.tags == ["language", "preference"]
    
    def test_add_with_embedding(self, db_store):
        """Test adding a context with an embedding."""
        context = ContextUnit(
            type=ContextType.FACT,
            content="The capital of France is Paris"
        )
        embedding = np.random.rand(384)
        
        db_store.add(context, embedding)
        retrieved_embedding = db_store.get_embedding(context.id)
        
        assert retrieved_embedding is not None
        assert retrieved_embedding.shape == (384,)
        np.testing.assert_array_almost_equal(retrieved_embedding, embedding)
    
    def test_list_all_contexts(self, db_store):
        """Test listing all contexts."""
        contexts = [
            ContextUnit(type=ContextType.PREFERENCE, content="Content 1"),
            ContextUnit(type=ContextType.GOAL, content="Content 2"),
            ContextUnit(type=ContextType.FACT, content="Content 3"),
        ]
        
        for ctx in contexts:
            db_store.add(ctx)
        
        all_contexts = db_store.list_all()
        assert len(all_contexts) == 3
    
    def test_list_exclude_superseded(self, db_store):
        """Test listing contexts excluding superseded ones."""
        context1 = ContextUnit(type=ContextType.PREFERENCE, content="Old preference")
        context2 = ContextUnit(type=ContextType.PREFERENCE, content="New preference")
        
        db_store.add(context1)
        db_store.add(context2)
        db_store.supersede(context1.id, context2.id)
        
        # Should only get active contexts
        active = db_store.list_all(include_superseded=False)
        assert len(active) == 1
        assert active[0].id == context2.id
        
        # Should get all contexts
        all_contexts = db_store.list_all(include_superseded=True)
        assert len(all_contexts) == 2
    
    def test_update_context(self, db_store):
        """Test updating a context."""
        context = ContextUnit(
            type=ContextType.GOAL,
            content="Original goal",
            confidence=0.8
        )
        
        db_store.add(context)
        
        updates = {
            "content": "Updated goal",
            "confidence": 0.95,
            "tags": ["updated"]
        }
        updated = db_store.update(context.id, updates)
        
        assert updated is not None
        assert updated.content == "Updated goal"
        assert updated.confidence == 0.95
        assert updated.tags == ["updated"]
    
    def test_update_nonexistent_context(self, db_store):
        """Test updating a context that doesn't exist."""
        result = db_store.update("nonexistent-id", {"content": "New"})
        assert result is None
    
    def test_delete_context(self, db_store):
        """Test deleting a context."""
        context = ContextUnit(
            type=ContextType.DECISION,
            content="A decision"
        )
        
        db_store.add(context)
        assert db_store.get(context.id) is not None
        
        success = db_store.delete(context.id)
        assert success is True
        assert db_store.get(context.id) is None
    
    def test_delete_nonexistent_context(self, db_store):
        """Test deleting a context that doesn't exist."""
        success = db_store.delete("nonexistent-id")
        assert success is False
    
    def test_supersede_context(self, db_store):
        """Test superseding a context."""
        old_context = ContextUnit(
            type=ContextType.PREFERENCE,
            content="Old preference"
        )
        new_context = ContextUnit(
            type=ContextType.PREFERENCE,
            content="New preference"
        )
        
        db_store.add(old_context)
        db_store.add(new_context)
        
        success = db_store.supersede(old_context.id, new_context.id)
        assert success is True
        
        retrieved = db_store.get(old_context.id)
        assert retrieved.status == ContextStatus.SUPERSEDED
        assert retrieved.superseded_by == new_context.id
    
    def test_update_embedding(self, db_store):
        """Test updating an embedding."""
        context = ContextUnit(
            type=ContextType.FACT,
            content="A fact"
        )
        embedding1 = np.random.rand(384)
        embedding2 = np.random.rand(384)
        
        db_store.add(context, embedding1)
        db_store.update_embedding(context.id, embedding2)
        
        retrieved = db_store.get_embedding(context.id)
        np.testing.assert_array_almost_equal(retrieved, embedding2)
    
    def test_list_with_embeddings(self, db_store):
        """Test listing contexts with their embeddings."""
        contexts = [
            ContextUnit(type=ContextType.PREFERENCE, content="Content 1"),
            ContextUnit(type=ContextType.GOAL, content="Content 2"),
        ]
        embeddings = [np.random.rand(384), np.random.rand(384)]
        
        for ctx, emb in zip(contexts, embeddings):
            db_store.add(ctx, emb)
        
        results = db_store.list_with_embeddings()
        assert len(results) == 2
        
        for ctx, emb in results:
            assert isinstance(ctx, ContextUnit)
            assert isinstance(emb, np.ndarray)
            assert emb.shape == (384,)

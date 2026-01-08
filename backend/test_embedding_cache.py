"""
Tests for embedding cache functionality.
"""
import pytest
import numpy as np
import time
from embedding_cache import EmbeddingCache


class TestEmbeddingCache:
    """Test suite for EmbeddingCache."""
    
    def test_cache_initialization(self):
        """Test cache initializes with correct parameters."""
        cache = EmbeddingCache(max_size=100, ttl_seconds=600)
        assert cache.max_size == 100
        assert cache.ttl_seconds == 600
        assert cache.size() == 0
    
    def test_cache_put_and_get(self):
        """Test basic put and get operations."""
        cache = EmbeddingCache()
        embedding = np.array([1.0, 2.0, 3.0])
        text = "test text"
        
        cache.put(text, embedding)
        retrieved = cache.get(text)
        
        assert retrieved is not None
        assert np.array_equal(retrieved, embedding)
    
    def test_cache_miss(self):
        """Test cache miss returns None."""
        cache = EmbeddingCache()
        retrieved = cache.get("non-existent text")
        assert retrieved is None
    
    def test_cache_expiration(self):
        """Test cache entries expire after TTL."""
        cache = EmbeddingCache(ttl_seconds=1)
        embedding = np.array([1.0, 2.0, 3.0])
        text = "test text"
        
        cache.put(text, embedding)
        assert cache.get(text) is not None
        
        # Wait for expiration
        time.sleep(1.1)
        assert cache.get(text) is None
    
    def test_cache_eviction(self):
        """Test cache evicts oldest entry when full."""
        cache = EmbeddingCache(max_size=2)
        
        embedding1 = np.array([1.0, 2.0, 3.0])
        embedding2 = np.array([4.0, 5.0, 6.0])
        embedding3 = np.array([7.0, 8.0, 9.0])
        
        cache.put("text1", embedding1)
        time.sleep(0.01)  # Ensure different timestamps
        cache.put("text2", embedding2)
        time.sleep(0.01)
        cache.put("text3", embedding3)
        
        # Cache should have text2 and text3, text1 should be evicted
        assert cache.size() == 2
        assert cache.get("text1") is None
        assert cache.get("text2") is not None
        assert cache.get("text3") is not None
    
    def test_cache_clear(self):
        """Test clearing cache."""
        cache = EmbeddingCache()
        
        cache.put("text1", np.array([1.0, 2.0, 3.0]))
        cache.put("text2", np.array([4.0, 5.0, 6.0]))
        
        assert cache.size() == 2
        cache.clear()
        assert cache.size() == 0
    
    def test_cache_stats(self):
        """Test cache statistics."""
        cache = EmbeddingCache(max_size=100, ttl_seconds=600)
        
        cache.put("text1", np.array([1.0, 2.0, 3.0]))
        cache.put("text2", np.array([4.0, 5.0, 6.0]))
        
        stats = cache.stats()
        assert stats["size"] == 2
        assert stats["max_size"] == 100
        assert stats["ttl_seconds"] == 600
    
    def test_same_text_returns_same_embedding(self):
        """Test that caching same text returns same embedding."""
        cache = EmbeddingCache()
        embedding = np.array([1.0, 2.0, 3.0])
        text = "test text"
        
        cache.put(text, embedding)
        retrieved1 = cache.get(text)
        retrieved2 = cache.get(text)
        
        assert np.array_equal(retrieved1, retrieved2)
        assert retrieved1 is retrieved2  # Should be same object
    
    def test_different_text_different_keys(self):
        """Test that different texts get different cache keys."""
        cache = EmbeddingCache()
        
        embedding1 = np.array([1.0, 2.0, 3.0])
        embedding2 = np.array([4.0, 5.0, 6.0])
        
        cache.put("text1", embedding1)
        cache.put("text2", embedding2)
        
        assert not np.array_equal(cache.get("text1"), cache.get("text2"))

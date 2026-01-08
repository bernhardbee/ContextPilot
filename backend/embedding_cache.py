"""
Embedding cache for storing and retrieving computed embeddings.
"""
from typing import Optional, Dict
import numpy as np
import hashlib
import time
from logger import logger


class EmbeddingCache:
    """In-memory cache for text embeddings with TTL support."""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """
        Initialize the embedding cache.
        
        Args:
            max_size: Maximum number of embeddings to cache
            ttl_seconds: Time-to-live for cached embeddings in seconds
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, tuple[np.ndarray, float]] = {}
        logger.info(f"Initialized EmbeddingCache (max_size={max_size}, ttl={ttl_seconds}s)")
    
    def _hash_text(self, text: str) -> str:
        """Generate cache key from text."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def get(self, text: str) -> Optional[np.ndarray]:
        """
        Retrieve embedding from cache.
        
        Args:
            text: Text to look up
            
        Returns:
            Cached embedding or None if not found/expired
        """
        key = self._hash_text(text)
        
        if key not in self.cache:
            return None
        
        embedding, timestamp = self.cache[key]
        
        # Check if expired
        if time.time() - timestamp > self.ttl_seconds:
            del self.cache[key]
            logger.debug(f"Cache entry expired for key {key[:8]}...")
            return None
        
        logger.debug(f"Cache hit for key {key[:8]}...")
        return embedding
    
    def put(self, text: str, embedding: np.ndarray):
        """
        Store embedding in cache.
        
        Args:
            text: Text being cached
            embedding: Embedding vector
        """
        key = self._hash_text(text)
        
        # Evict oldest entry if cache is full
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.items(), key=lambda x: x[1][1])[0]
            del self.cache[oldest_key]
            logger.debug(f"Evicted oldest cache entry")
        
        self.cache[key] = (embedding, time.time())
        logger.debug(f"Cached embedding for key {key[:8]}...")
    
    def clear(self):
        """Clear all cached embeddings."""
        self.cache.clear()
        logger.info("Cleared embedding cache")
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self.cache)
    
    def stats(self) -> dict:
        """Get cache statistics."""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds
        }

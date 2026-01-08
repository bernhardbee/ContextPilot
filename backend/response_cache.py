"""
API response caching for read-only endpoints.
"""
import time
import hashlib
import json
from typing import Any, Optional, Dict, Tuple
from functools import wraps
from fastapi import Request
from logger import logger


class ResponseCache:
    """Simple in-memory cache for API responses."""
    
    def __init__(self, default_ttl: int = 300, max_size: int = 100):
        """
        Initialize response cache.
        
        Args:
            default_ttl: Default time-to-live in seconds
            max_size: Maximum number of cached responses
        """
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.cache: Dict[str, Tuple[Any, float]] = {}
        logger.info(f"Initialized ResponseCache (ttl={default_ttl}s, max_size={max_size})")
    
    def _generate_key(self, request: Request, *args, **kwargs) -> str:
        """Generate cache key from request and parameters."""
        key_data = {
            "path": str(request.url.path),
            "query": str(request.url.query),
            "args": args,
            "kwargs": {k: v for k, v in kwargs.items() if k != "request"}
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get cached response.
        
        Args:
            key: Cache key
            
        Returns:
            Cached response or None if expired/not found
        """
        if key not in self.cache:
            return None
        
        response, timestamp = self.cache[key]
        
        # Check if expired
        if time.time() - timestamp > self.default_ttl:
            del self.cache[key]
            logger.debug(f"Cache expired for key {key[:8]}...")
            return None
        
        logger.debug(f"Cache hit for key {key[:8]}...")
        return response
    
    def set(self, key: str, response: Any):
        """
        Cache a response.
        
        Args:
            key: Cache key
            response: Response to cache
        """
        # Evict oldest if full
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.items(), key=lambda x: x[1][1])[0]
            del self.cache[oldest_key]
            logger.debug("Evicted oldest cache entry")
        
        self.cache[key] = (response, time.time())
        logger.debug(f"Cached response for key {key[:8]}...")
    
    def clear(self):
        """Clear all cached responses."""
        self.cache.clear()
        logger.info("Cleared response cache")
    
    def invalidate(self, pattern: str = None):
        """
        Invalidate cache entries.
        
        Args:
            pattern: If provided, only invalidate keys containing this pattern
        """
        if pattern is None:
            self.clear()
            return
        
        keys_to_delete = [k for k in self.cache.keys() if pattern in k]
        for key in keys_to_delete:
            del self.cache[key]
        logger.info(f"Invalidated {len(keys_to_delete)} cache entries")
    
    def stats(self) -> dict:
        """Get cache statistics."""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "default_ttl": self.default_ttl
        }


# Global cache instance
response_cache = ResponseCache(default_ttl=300, max_size=100)


def cached(ttl: int = None):
    """
    Decorator to cache endpoint responses.
    
    Args:
        ttl: Time-to-live in seconds (uses default if None)
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(request: Request, *args, **kwargs):
            # Generate cache key
            cache_key = response_cache._generate_key(request, *args, **kwargs)
            
            # Try to get from cache
            cached_response = response_cache.get(cache_key)
            if cached_response is not None:
                return cached_response
            
            # Call the function
            response = await func(request, *args, **kwargs)
            
            # Cache the response
            response_cache.set(cache_key, response)
            
            return response
        
        @wraps(func)
        def sync_wrapper(request: Request, *args, **kwargs):
            # Generate cache key
            cache_key = response_cache._generate_key(request, *args, **kwargs)
            
            # Try to get from cache
            cached_response = response_cache.get(cache_key)
            if cached_response is not None:
                return cached_response
            
            # Call the function
            response = func(request, *args, **kwargs)
            
            # Cache the response
            response_cache.set(cache_key, response)
            
            return response
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

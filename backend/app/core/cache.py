from functools import lru_cache, wraps
from typing import Any, Callable, Optional, Dict
from datetime import datetime, timedelta
import hashlib
import json
import redis
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """
    A cache manager that provides both memory and distributed caching capabilities.
    Supports both in-memory and Redis caching.
    """
    
    def __init__(self, ttl: int = 300, use_redis: bool = True):
        self.ttl = ttl
        self.use_redis = use_redis
        self._cache = {}
        self._timestamps = {}
        
        # Initialize Redis connection if enabled
        if use_redis:
            try:
                self.redis = redis.Redis(
                    host='localhost',
                    port=6379,
                    db=0,
                    decode_responses=True
                )
                self.redis.ping()  # Test connection
            except redis.ConnectionError:
                logger.warning("Redis connection failed. Falling back to in-memory cache.")
                self.use_redis = False

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a unique cache key with prefix."""
        key_parts = [prefix]
        key_parts.extend([str(arg) for arg in args])
        key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _is_expired(self, key: str) -> bool:
        """Check if a cached item has expired."""
        if self.use_redis:
            ttl = self.redis.ttl(key)
            return ttl <= 0
        
        if key not in self._timestamps:
            return True
        return (datetime.utcnow() - self._timestamps[key]).total_seconds() > self.ttl

    def get(self, key: str) -> Optional[Any]:
        """Retrieve an item from cache."""
        if self.use_redis:
            data = self.redis.get(key)
            if data:
                return json.loads(data)
            return None
            
        if key in self._cache and not self._is_expired(key):
            return self._cache[key]
        self.invalidate(key)
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store an item in cache with optional custom TTL."""
        if ttl is None:
            ttl = self.ttl
            
        if self.use_redis:
            try:
                self.redis.setex(
                    key,
                    ttl,
                    json.dumps(value)
                )
            except redis.RedisError as e:
                logger.error(f"Redis error while setting key {key}: {str(e)}")
                # Fallback to memory cache
                self._cache[key] = value
                self._timestamps[key] = datetime.utcnow()
        else:
            self._cache[key] = value
            self._timestamps[key] = datetime.utcnow()

    def invalidate(self, key: str) -> None:
        """Remove an item from cache."""
        if self.use_redis:
            self.redis.delete(key)
        else:
            self._cache.pop(key, None)
            self._timestamps.pop(key, None)

    def clear(self) -> None:
        """Clear all cached items."""
        if self.use_redis:
            self.redis.flushdb()
        self._cache.clear()
        self._timestamps.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            'local_cache_size': len(self._cache),
            'redis_available': self.use_redis
        }
        
        if self.use_redis:
            try:
                info = self.redis.info()
                stats.update({
                    'redis_used_memory': info['used_memory_human'],
                    'redis_hits': info['keyspace_hits'],
                    'redis_misses': info['keyspace_misses'],
                    'redis_keys': self.redis.dbsize(),
                    'redis_connected_clients': info['connected_clients']
                })
            except redis.RedisError as e:
                stats['redis_error'] = str(e)
        
        return stats

    def get_key_info(self, key: str) -> Dict[str, Any]:
        """Get detailed information about a specific cached key."""
        info = {
            'exists': False,
            'expired': True,
            'ttl': None,
            'size': 0
        }
        
        if self.use_redis:
            if self.redis.exists(key):
                info.update({
                    'exists': True,
                    'expired': self.redis.ttl(key) <= 0,
                    'ttl': self.redis.ttl(key),
                    'size': len(self.redis.get(key) or '')
                })
        else:
            if key in self._cache:
                info.update({
                    'exists': True,
                    'expired': self._is_expired(key),
                    'ttl': self.ttl - (datetime.utcnow() - self._timestamps[key]).total_seconds() if key in self._timestamps else None,
                    'size': len(str(self._cache[key]))
                })
        
        return info


def cached(ttl: int = 300, prefix: str = ''):
    """
    Decorator that caches function results with a specified TTL.
    
    Args:
        ttl (int): Time to live in seconds. Defaults to 300 (5 minutes).
        prefix (str): Optional prefix for cache keys.
    """
    cache_manager = CacheManager(ttl=ttl)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key with optional prefix
            cache_key = cache_manager._generate_key(prefix or func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # If not in cache, call function
            result = await func(*args, **kwargs)
            
            # Store in cache
            cache_manager.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator
# app/core/cache.py
from functools import lru_cache, wraps
from typing import Any, Callable, Optional, Dict
from datetime import datetime, timedelta
import hashlib
import json
import redis
import logging
from datetime import timedelta
from time import time
from app.core.config import settings

logger = logging.getLogger(__name__)

class CacheManager:
    """
    Production-ready cache manager for djangifynews.up.railway.app
    """
    
    def __init__(self, ttl: int = 300):
        self.ttl = ttl
        self._cache = {}
        self._timestamps = {}
        
        # Production Redis settings
        self.redis_host = 'localhost'
        self.redis_port = 6379
        self.redis_db = 0

        # Initialize Redis connection
        try:
            self.redis = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                decode_responses=True,
                socket_timeout=5,
                retry_on_timeout=True,
                socket_keepalive=True,
                health_check_interval=30
            )
            # Test connection
            self.redis.ping()
            self.use_redis = True
            logger.info(f"Successfully connected to Redis on {self.redis_host}")
        except redis.ConnectionError as e:
            logger.warning(f"Redis connection failed: {str(e)}. Falling back to in-memory cache.")
            self.use_redis = False
        except Exception as e:
            logger.error(f"Unexpected Redis error: {str(e)}")
            self.use_redis = False

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a unique cache key with production namespace."""
        key_parts = [prefix]
        key_parts.extend([str(arg) for arg in args])
        key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
        key_string = "|".join(key_parts)
        return f"newsapi:prod:{hashlib.md5(key_string.encode()).hexdigest()}"

    def get(self, key: str) -> Optional[Any]:
        """Retrieve an item from cache with rate limiting."""
        if not self.check_rate_limit('cache_reads'):
            logger.warning("Cache read rate limit exceeded")
            return None

        if not self.use_redis:
            if key in self._cache and not self._is_expired(key):
                return self._cache[key]
            return None

        try:
            data = self.redis.get(key)
            if data:
                return json.loads(data)
        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.error(f"Production Redis error - get: {str(e)}")
            self._fallback_to_memory()
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store an item in cache with rate limiting."""
        if not self.check_rate_limit('cache_writes'):
            logger.warning("Cache write rate limit exceeded")
            return False

        if ttl is None:
            ttl = self.ttl
        if not self.use_redis:
            self._cache[key] = value
            self._timestamps[key] = datetime.utcnow()
            return True

        try:
            return self.redis.setex(
                name=key,
                time=ttl,
                value=json.dumps(value)
            )
        except redis.RedisError as e:
            logger.error(f"Production Redis error - set: {str(e)}")
            self._fallback_to_memory()
            return False

    def _is_expired(self, key: str) -> bool:
        """Check if a cached item has expired (for in-memory cache)."""
        if key not in self._timestamps:
            return True
        age = (datetime.utcnow() - self._timestamps[key]).total_seconds()
        return age > self.ttl

    def _fallback_to_memory(self):
        """Handle Redis failures in production."""
        self.use_redis = False
        logger.critical("Production Redis failure - falling back to memory cache")

    def clear(self) -> None:
        """Clear production cache safely."""
        if not self.use_redis:
            self._cache.clear()
            self._timestamps.clear()
            return

        try:
            # Only clear keys with our production prefix
            for key in self.redis.scan_iter("newsapi:prod:*"):
                self.redis.delete(key)
        except redis.RedisError as e:
            logger.error(f"Production Redis error - clear: {str(e)}")
            self._fallback_to_memory()


    def _get_rate_limit_key(self, key_prefix: str) -> str:
        """Generate rate limit key with production namespace."""
        return f"newsapi:ratelimit:{key_prefix}"

    def check_rate_limit(
        self, 
        key_prefix: str, 
        max_requests: int = 1000,
        interval: int = 3600
    ) -> bool:
        """
        Check if rate limit is exceeded.
        
        Args:
            key_prefix: Identifier for the rate limit (e.g., 'cache_reads', 'cache_writes')
            max_requests: Maximum number of requests allowed in the interval
            interval: Time interval in seconds (default 1 hour)
        """
        if not self.use_redis:
            return True  # Skip rate limiting if Redis is not available
            
        try:
            rate_key = self._get_rate_limit_key(key_prefix)
            current = time()
            pipeline = self.redis.pipeline()
            
            # Remove counts older than the interval
            pipeline.zremrangebyscore(rate_key, 0, current - interval)
            # Add current request
            pipeline.zadd(rate_key, {str(current): current})
            # Count requests in current window
            pipeline.zcard(rate_key)
            # Set expiry on rate limit key
            pipeline.expire(rate_key, interval)
            
            _, _, request_count, _ = pipeline.execute()
            
            return request_count <= max_requests
        except redis.RedisError as e:
            logger.error(f"Rate limit check failed: {str(e)}")
            return True  # Allow operation on Redis failure

    def increment_rate_limit(self, key_prefix: str) -> None:
        """Increment rate limit counter."""
        if not self.use_redis:
            return
            
        try:
            rate_key = self._get_rate_limit_key(key_prefix)
            current = time()
            self.redis.zadd(rate_key, {str(current): current})
        except redis.RedisError as e:
            logger.error(f"Rate limit increment failed: {str(e)}")



    def get_stats(self) -> Dict[str, Any]:
        """Get production cache statistics."""
        stats = {
            'environment': 'production',
            'type': 'redis' if self.use_redis else 'memory',
            'status': 'connected' if self.use_redis else 'fallback'
        }

        if self.use_redis:
            try:
                info = self.redis.info()
                stats.update({
                    'used_memory': info.get('used_memory_human'),
                    'connected_clients': info.get('connected_clients'),
                    'uptime_days': info.get('uptime_in_days'),
                    'hits': info.get('keyspace_hits'),
                    'misses': info.get('keyspace_misses'),
                    'host': self.redis_host
                })
            except redis.RedisError as e:
                stats['error'] = str(e)

        return stats

# Production cache decorator
def cached(ttl: int = 300, prefix: str = ''):
    """Production-ready cache decorator."""
    cache_manager = CacheManager(ttl=ttl)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = cache_manager._generate_key(prefix or func.__name__, *args, **kwargs)
            
            try:
                cached_value = cache_manager.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                result = await func(*args, **kwargs)
                cache_manager.set(cache_key, result, ttl)
                return result
            except Exception as e:
                logger.error(f"Production cache error in {func.__name__}: {str(e)}")
                return await func(*args, **kwargs)
                
        return wrapper
    return decorator
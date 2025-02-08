# backend/app/core/redis_cache.py

import redis
import time
import json
import logging
from typing import Any, Optional
from functools import wraps
from .config import settings

logger = logging.getLogger(__name__)

class RedisCache:
    def __init__(self):
        self.client = None
        self.fallback_cache = {}
        self.connect()

    def connect(self) -> None:
        """Establish Redis connection with error handling"""
        try:
            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                ssl=settings.REDIS_SSL,
                socket_timeout=settings.REDIS_TIMEOUT,
                decode_responses=True
            )
            # Test connection
            self.client.ping()
        except redis.ConnectionError as e:
            logger.warning(f"Redis connection failed: {str(e)}. Using fallback cache.")
            self.client = None

    def set_cache(self, key: str, value: Any, ttl: int = None) -> None:
        """Set cache with fallback to memory cache"""
        if ttl is None:
            ttl = settings.CACHE_TTL
        
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            if self.client:
                self.client.setex(key, ttl, value)
            else:
                self.fallback_cache[key] = {
                    'value': value,
                    'expires': time.time() + ttl
                }
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")

    def get_cache(self, key: str) -> Optional[Any]:
        """Get cache with fallback to memory cache"""
        try:
            if self.client:
                value = self.client.get(key)
                if value:
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        return value
            else:
                cache_data = self.fallback_cache.get(key)
                if cache_data and time.time() < cache_data['expires']:
                    return cache_data['value']
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
        return None

    def delete_cache(self, key: str) -> None:
        """Delete cache with fallback"""
        try:
            if self.client:
                self.client.delete(key)
            else:
                self.fallback_cache.pop(key, None)
        except Exception as e:
            logger.error(f"Cache delete error: {str(e)}")

    def is_rate_limited(self, user_id: str, limit: int, window: int) -> bool:
        """Check rate limiting with fallback"""
        try:
            if self.client:
                current_window = int(time.time() // window)
                key = f"rate:{user_id}:{current_window}"
                requests = self.client.incr(key)
                if requests == 1:
                    self.client.expire(key, window)
                return requests > limit
        except Exception as e:
            logger.error(f"Rate limit check error: {str(e)}")
        return False  # Fail open if Redis is unavailable

# Create singleton instance
cache = RedisCache()

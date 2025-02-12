# app/core/rate_limit.py
from fastapi import HTTPException, Request
from redis import Redis
from typing import Optional
from app.core.config import settings
import logging


logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, redis_client: Optional[Redis] = None):
        try:
            self.redis = redis_client or Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                ssl=settings.REDIS_SSL,
                socket_timeout=settings.REDIS_TIMEOUT,
                decode_responses=True
            )
            # Test connection
            self.redis.ping()
        except Exception as e:
            logger.warning(f"Redis connection failed: {str(e)}. Using in-memory rate limiting.")
            self.redis = None

        self.rate_limit = settings.API_RATE_LIMIT
        self.window = settings.API_RATE_LIMIT_WINDOW

    async def check_rate_limit(self, request: Request):
        client_ip = request.client.host
        key = f"rate_limit:{client_ip}"
        
        try:
            if self.redis:
                current = self.redis.get(key)
                if current is None:
                    self.redis.setex(key, self.window, 1)
                    return True
                    
                if int(current) >= self.rate_limit:
                    raise HTTPException(
                        status_code=429,
                        detail="Rate limit exceeded. Please try again later."
                    )
                    
                self.redis.incr(key)
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Rate limit check error: {str(e)}")
            return True  # Fail open if Redis is unavailable

rate_limiter = RateLimiter()

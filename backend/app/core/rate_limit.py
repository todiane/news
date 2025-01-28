# app/core/rate_limit.py

from fastapi import HTTPException, Request
from redis import Redis
import time
from typing import Optional
from app.core.config import settings

class RateLimiter:
    def __init__(self, redis_client: Optional[Redis] = None):
        self.redis = redis_client or Redis(host='localhost', port=6379, db=0)
        self.rate_limit = 100  # requests per window
        self.window = 3600    # window in seconds (1 hour)

    async def check_rate_limit(self, request: Request):
        client_ip = request.client.host
        key = f"rate_limit:{client_ip}"
        
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

rate_limiter = RateLimiter()
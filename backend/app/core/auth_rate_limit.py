from fastapi import HTTPException, Request
from redis import Redis
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

class AuthRateLimiter:
    def __init__(self):
        self.redis = Redis(host='localhost', port=6379, db=0)
        self.login_limits = {
            'max_attempts': 5,        # Maximum login attempts
            'window_seconds': 300,    # Time window in seconds (5 minutes)
            'block_duration': 1800    # Block duration in seconds (30 minutes)
        }

    async def check_login_attempt(self, ip_address: str, email: str) -> None:
        """Check if login should be allowed based on previous attempts"""
        # Check if IP is blocked
        ip_key = f"auth:blocked:{ip_address}"
        if self.redis.get(ip_key):
            raise HTTPException(
                status_code=429,
                detail={
                    "message": "Too many failed attempts. Please try again later.",
                    "wait_time": self.redis.ttl(ip_key)
                }
            )

        # Check attempts count
        attempts_key = f"auth:attempts:{ip_address}:{email}"
        attempts = self.redis.get(attempts_key)
        
        if attempts and int(attempts) >= self.login_limits['max_attempts']:
            # Block the IP
            self.redis.setex(
                ip_key,
                self.login_limits['block_duration'],
                1
            )
            # Reset attempts counter
            self.redis.delete(attempts_key)
            raise HTTPException(
                status_code=429,
                detail={
                    "message": "Too many failed attempts. Please try again later.",
                    "wait_time": self.login_limits['block_duration']
                }
            )

    async def record_failed_attempt(self, ip_address: str, email: str) -> None:
        """Record a failed login attempt"""
        attempts_key = f"auth:attempts:{ip_address}:{email}"
        pipe = self.redis.pipeline()
        
        # Increment attempts counter
        pipe.incr(attempts_key)
        # Set expiry if not already set
        pipe.expire(attempts_key, self.login_limits['window_seconds'])
        
        pipe.execute()

    async def clear_attempts(self, ip_address: str, email: str) -> None:
        """Clear failed attempts after successful login"""
        attempts_key = f"auth:attempts:{ip_address}:{email}"
        self.redis.delete(attempts_key)

    async def check_registration_rate(self, ip_address: str) -> None:
        """Limit number of registrations from same IP"""
        key = f"auth:registration:{ip_address}"
        if self.redis.get(key):
            raise HTTPException(
                status_code=429,
                detail="Please wait before creating another account"
            )
        
        # Set registration cooldown (1 hour)
        self.redis.setex(key, 3600, 1)

auth_rate_limiter = AuthRateLimiter()

# app/core/config.py

from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path
from functools import lru_cache

from urllib.parse import urlparse

class Settings(BaseSettings):
   PROJECT_NAME: str = "News Aggregator API"
   VERSION: str = "1.0.0"
   DEBUG: bool = False
   
   SERVER_HOST: str = "djangifynews.up.railway.app"
   HTTPS_ONLY: bool = True

   BACKEND_CORS_ORIGINS: str = "*"

   DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/news")
   
   SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
   ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
   ALGORITHM: str = "HS256"
   
   SECURITY_HEADERS: dict = {
       "X-Frame-Options": "DENY",
       "X-Content-Type-Options": "nosniff",
       "X-XSS-Protection": "1; mode=block",
       "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
       "Content-Security-Policy": "default-src 'self'; img-src 'self' data: https:; script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; font-src 'self' data: https://cdnjs.cloudflare.com;",
       "Referrer-Policy": "strict-origin-when-cross-origin",
       "Permissions-Policy": "camera=(), microphone=(), geolocation=(), interest-cohort=()"
   }
   
   MAIL_USERNAME: str = os.getenv("MAIL_USERNAME", "")
   MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD", "")
   MAIL_FROM: str = os.getenv("MAIL_FROM", "")
   MAIL_PORT: int = int(os.getenv("MAIL_PORT", 587))
   MAIL_SERVER: str = os.getenv("MAIL_SERVER", "")
   MAIL_FROM_NAME: str = os.getenv("MAIL_FROM_NAME", "C.A.D. News Feed")
   MAIL_TLS: bool = True
   MAIL_SSL: bool = False
   MAIL_SSL_TLS: bool = True
   USE_CREDENTIALS: bool = True
   MAIL_STARTTLS: bool = False
   
   REDIS_HOST: str = os.getenv("REDISHOST", "localhost")
   REDIS_PORT: int = int(os.getenv("REDISPORT", 6379))
   REDIS_DB: int = int(os.getenv("REDIS_DB", 0))
   REDIS_PASSWORD: Optional[str] = os.getenv("REDISPASSWORD")
   REDIS_URL: Optional[str] = os.getenv("REDIS_URL")
   REDIS_SSL: bool = os.getenv("REDIS_SSL", "true").lower() == "true"
   REDIS_TIMEOUT: int = int(os.getenv("REDIS_TIMEOUT", 5))

   @property
   def redis_url(self) -> str:
        """Get Redis URL with proper format for production/development"""
        if self.REDIS_URL:
            # Parse provided REDIS_URL to ensure proper format
            parsed = urlparse(self.REDIS_URL)
            return f"rediss://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}/{self.REDIS_DB}"
        
        # Fallback for development
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        protocol = "rediss" if self.REDIS_SSL else "redis"
        return f"{protocol}://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

   def get_redis_options(self) -> dict:
        """Get Redis connection options"""
        return {
            "host": self.REDIS_HOST,
            "port": self.REDIS_PORT,
            "db": self.REDIS_DB,
            "password": self.REDIS_PASSWORD,
            "ssl": self.REDIS_SSL,
            "socket_timeout": self.REDIS_TIMEOUT,
            "retry_on_timeout": True,
            "health_check_interval": 30,
            "decode_responses": True
        }
   
   CACHE_TTL: int = 3600
   
   LOGIN_RATE_LIMIT: int = 5
   LOGIN_RATE_LIMIT_WINDOW: int = 300
   REGISTRATION_RATE_LIMIT: int = 3
   API_RATE_LIMIT: int = 100
   API_RATE_LIMIT_WINDOW: int = 60

   class Config:
       env_file = ".env"
       case_sensitive = True
   
   @property
   def is_production(self) -> bool:
       return not self.DEBUG and "railway.app" in self.SERVER_HOST

   def validate_https(self) -> None:
       if self.is_production and not self.HTTPS_ONLY:
           raise ValueError("HTTPS must be enabled in production")

@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    if settings.is_production:
        settings.validate_https()
    return settings

settings = get_settings()


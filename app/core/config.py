# app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional
import os
from urllib.parse import urlparse

class Settings(BaseSettings):
    PROJECT_NAME: str = "News API"
    VERSION: str = "1.0.0"
    SERVER_HOST: str = "djangifynews.up.railway.app"
    BACKEND_CORS_ORIGINS: str = "https://djangifynews.up.railway.app"

    DATABASE_URL: str = os.getenv("DATABASE_PUBLIC_URL")
    SECRET_KEY: str = os.getenv("SECRET_KEY")
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
    
    MAIL_USERNAME: str = os.getenv("MAIL_USERNAME", "newsapi@djangify.com")
    MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD", "")
    MAIL_FROM: str = os.getenv("MAIL_FROM", "newsapi@djangify.com")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", "587"))
    MAIL_SERVER: str = os.getenv("MAIL_SERVER", "mail.djangify.com")
    MAIL_FROM_NAME: str = os.getenv("MAIL_FROM_NAME", "News API")
    MAIL_TLS: bool = True
    MAIL_SSL: bool = False
    MAIL_SSL_TLS: bool = True
    USE_CREDENTIALS: bool = True
    
    REDIS_HOST: str = os.getenv("REDISHOST")
    REDIS_PORT: int = int(os.getenv("REDISPORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDISPASSWORD")
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")
    REDIS_SSL: bool = True
    REDIS_TIMEOUT: int = int(os.getenv("REDIS_TIMEOUT", "5"))

    @property
    def redis_url(self) -> str:
        if self.REDIS_URL:
            parsed = urlparse(self.REDIS_URL)
            return f"rediss://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}/{self.REDIS_DB}"
        return f"rediss://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    def get_redis_options(self) -> dict:
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

settings = Settings()

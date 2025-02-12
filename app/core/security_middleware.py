# app/core/security_middleware.py

import re
import html
from typing import Callable, Dict, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.exc import SQLAlchemyError
import logging
from .config import settings

logger = logging.getLogger(__name__)

class SecurityMiddleware:
    """Security middleware for input sanitization, XSS protection and SQL injection prevention"""
    
    def __init__(self):
        self.xss_pattern = re.compile(r'<[^>]*?>')
        self.sql_pattern = re.compile(r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|EXEC|--)\b)', re.IGNORECASE)
        
    async def sanitize_input(self, request: Request) -> Dict:
        """Sanitize input data from request"""
        content_type = request.headers.get('content-type', '')
        
        if 'application/json' in content_type:
            try:
                json_data = await request.json()
                return self._sanitize_dict(json_data)
            except Exception as e:
                logger.error(f"Error sanitizing JSON input: {str(e)}")
                return {}
                
        elif 'application/x-www-form-urlencoded' in content_type:
            form_data = await request.form()
            return {key: self._sanitize_value(value) for key, value in form_data.items()}
            
        return {}

    def _sanitize_dict(self, data: Dict) -> Dict:
        """Recursively sanitize dictionary values"""
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [self._sanitize_value(item) for item in value]
            else:
                sanitized[key] = self._sanitize_value(value)
        return sanitized

    def _sanitize_value(self, value: any) -> str:
        """Sanitize individual value"""
        if not isinstance(value, (str, bytes)):
            return value
            
        # Convert to string if bytes
        if isinstance(value, bytes):
            value = value.decode('utf-8')
            
        # HTML escape
        value = html.escape(value)
        
        # Remove potential XSS
        value = self.xss_pattern.sub('', value)
        
        # Check for SQL injection attempts
        if self.sql_pattern.search(value):
            logger.warning(f"Potential SQL injection attempt detected: {value}")
            return ''
            
        return value

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Middleware implementation"""
        try:
            # Skip sanitization for specific paths
            if any(path in request.url.path for path in ['/docs', '/redoc', '/openapi.json']):
                return await call_next(request)

            # Sanitize input
            sanitized_data = await self.sanitize_input(request)
            
            # Store sanitized data in request state
            request.state.sanitized_data = sanitized_data
            
            # Process request
            response = await call_next(request)
            
            # Add security headers
            for header, value in settings.SECURITY_HEADERS.items():
                response.headers[header] = value
                
            return response
            
        except Exception as e:
            logger.error(f"Security middleware error: {str(e)}")
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid input data"}
            )

# SQL Injection Prevention for SQLAlchemy
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite connection parameters for security"""
    # Disable potentially dangerous operations
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

# Create middleware instance
security_middleware = SecurityMiddleware()

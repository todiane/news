# app/core/middleware.py
import uuid
from fastapi import Request
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import BaseMiddleware
from .rate_limit import rate_limiter

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        await rate_limiter.check_rate_limit(request)
        response = await call_next(request)
        return response
    

class RequestIDMiddleware(BaseMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.request_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response
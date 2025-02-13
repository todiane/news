# app/core/middleware.py
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from .rate_limit import rate_limiter
from fastapi import status
from fastapi.responses import JSONResponse, RedirectResponse
import logging

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            await rate_limiter.check_rate_limit(request)
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"Rate limit middleware error: {str(e)}")
            raise e

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.request_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

# Add after the existing middleware classes
class AuthenticationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        protected_routes = {'/reader', '/feeds', '/profile'}
        path = request.url.path
        
        if path in protected_routes:
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                if "application/json" in request.headers.get("accept", ""):
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"detail": "Not authenticated"}
                    )
                return RedirectResponse(url='/login')
        
        response = await call_next(request)
        return response
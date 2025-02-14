# app/core/auth_middleware.py

from typing import Optional, List
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from datetime import datetime
import logging
from app.core.config import settings
from app.models.user import User
from app.db.session import get_db
from sqlalchemy.orm import Session
from app.crud.user import user as user_crud

logger = logging.getLogger(__name__)

class JWTAuthMiddleware:
    """Middleware for JWT token validation and role-based access control"""
    
    def __init__(self):
        self.security = HTTPBearer()
        self.exempt_paths = {
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/forgot-password",
            "/api/v1/auth/reset-password",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json"
        }
        # Add static file paths
        self.exempt_paths.update({"/static", "/favicon.ico"})
        
    async def __call__(self, request: Request, call_next):
        # Skip authentication for exempt paths
        if self._is_path_exempt(request.url.path):
            return await call_next(request)

        try:
            # Get and validate JWT token
            token = await self._get_token(request)
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing authentication token",
                    headers={"WWW-Authenticate": "Bearer"}
                )

            # Validate and decode token
            payload = self._validate_token(token)
            
            # Get user from database
            user = await self._get_user(payload.get("sub"))
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )

            # Store user in request state
            request.state.user = user
            
            # Check role-based access
            if not self._check_role_access(user, request.url.path):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough privileges"
                )

            response = await call_next(request)
            return response

        except JWTError as e:
            logger.error(f"JWT validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )

    def _is_path_exempt(self, path: str) -> bool:
        """Check if path is exempt from authentication"""
        return any(path.startswith(exempt) for exempt in self.exempt_paths)

    async def _get_token(self, request: Request) -> Optional[str]:
        """Extract JWT token from request"""
        try:
            auth = await self.security(request)
            return auth.credentials if auth else None
        except:
            # Handle cases where Authorization header is malformed
            return None

    def _validate_token(self, token: str) -> dict:
        """Validate and decode JWT token"""
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            
            # Check token expiration
            exp = payload.get("exp")
            if exp and datetime.utcnow().timestamp() > exp:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired"
                )
                
            return payload
            
        except JWTError as e:
            logger.error(f"Token validation error: {str(e)}")
            raise

    async def _get_user(self, user_id: str) -> Optional[User]:
        """Get user from database"""
        if not user_id:
            return None
            
        try:
            db: Session = next(get_db())
            return user_crud.get(db, id=int(user_id))
        except Exception as e:
            logger.error(f"Error fetching user: {str(e)}")
            return None

    def _check_role_access(self, user: User, path: str) -> bool:
        """Check if user has required role for path"""
        # Admin paths require admin role
        admin_paths = {"/api/v1/admin", "/api/v1/users"}
        if any(path.startswith(p) for p in admin_paths):
            return user.is_admin

        # Add more role checks as needed
        return True

class RoleBasedAccessControl:
    """Role-based access control middleware"""
    
    def __init__(self):
        self.role_permissions = {
            "admin": {"read", "write", "delete", "manage_users"},
            "moderator": {"read", "write"},
            "user": {"read"}
        }
        
    def has_permission(self, user: User, required_permission: str) -> bool:
        """Check if user has required permission"""
        if user.is_admin:
            return True
            
        user_role = "user"  # Default role
        if hasattr(user, "role"):
            user_role = user.role
            
        allowed_permissions = self.role_permissions.get(user_role, set())
        return required_permission in allowed_permissions

    async def __call__(self, request: Request, call_next):
        # Skip RBAC for public endpoints
        if request.url.path.startswith(("/public", "/api/v1/auth")):
            return await call_next(request)

        try:
            user = getattr(request.state, "user", None)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            # Determine required permission based on path and method
            required_permission = self._get_required_permission(
                request.method,
                request.url.path
            )
            
            if not self.has_permission(user, required_permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough privileges"
                )

            return await call_next(request)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"RBAC error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authorization error"
            )

    def _get_required_permission(self, method: str, path: str) -> str:
        """Determine required permission based on HTTP method and path"""
        if method == "GET":
            return "read"
        elif method in {"POST", "PUT", "PATCH"}:
            return "write"
        elif method == "DELETE":
            return "delete"
        return "read"  # Default to read permission

# Create middleware instances
jwt_middleware = JWTAuthMiddleware()
rbac = RoleBasedAccessControl()

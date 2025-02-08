# backend/app/core/auth_decorators.py

from functools import wraps
from typing import List, Optional, Callable
from fastapi import HTTPException, status, Request
from app.models.user import User

def require_roles(roles: List[str]):
    """Decorator to require specific roles for endpoint access"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = next((arg for arg in args if isinstance(arg, Request)), None)
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )

            user: Optional[User] = getattr(request.state, "user", None)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            # Admin always has access
            if user.is_admin:
                return await func(*args, **kwargs)

            user_role = getattr(user, "role", "user")
            if user_role not in roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough privileges"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_permissions(permissions: List[str]):
    """Decorator to require specific permissions for endpoint access"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = next((arg for arg in args if isinstance(arg, Request)), None)
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )

            user: Optional[User] = getattr(request.state, "user", None)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            # Admin always has all permissions
            if user.is_admin:
                return await func(*args, **kwargs)

            user_permissions = getattr(user, "permissions", set())
            if not all(perm in user_permissions for perm in permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough privileges"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator

def admin_only():
    """Decorator to restrict endpoint access to admin users only"""
    return require_roles(["admin"])

def moderator_or_above():
    """Decorator to restrict endpoint access to moderators and admins"""
    return require_roles(["admin", "moderator"])

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from jose import jwt

from app.db.base import get_db
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.core.password import validate_password, PasswordValidationError
from app.core.email import email_manager
from app.core.auth_rate_limit import auth_rate_limiter
from app.crud.user import user
from app.schemas.user import UserCreate, User, Token, PasswordReset
from app.core.versioning import version_config, APIVersion, VersionedResponse
from app.core.error_handler import ErrorDetail
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class AuthResponse(VersionedResponse):
    data: dict

@router.post("/register", response_model=AuthResponse)
async def register_user(
    request: Request,
    user_in: UserCreate,
    db: Session = Depends(get_db),
    api_version: str = Depends(version_config.verify_version)
):
    """
    Register a new user with email verification.
    
    Version changes:
    - 1.0: Base implementation
    - 1.1: Added password strength validation
    - 2.0: Added social registration options
    """
    try:
        # Check registration rate limit
        await auth_rate_limiter.check_registration_rate(request.client.host)
        
        # Validate email
        if user.get_by_email(db, email=user_in.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorDetail(
                    code="EMAIL_EXISTS",
                    message="Email already registered",
                    details={"email": user_in.email} if version_config.is_supported(api_version) else None
                ).dict()
            )
        
        # Validate password
        try:
            password_check = validate_password(user_in.password)
            if not password_check.is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ErrorDetail(
                        code="INVALID_PASSWORD",
                        message="Password does not meet requirements",
                        details={"suggestions": password_check.suggestions} if version_config.is_supported(api_version) else None
                    ).dict()
                )
        except PasswordValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorDetail(
                    code="PASSWORD_VALIDATION_ERROR",
                    message=str(e),
                    details={"errors": e.errors} if version_config.is_supported(api_version) else None
                ).dict()
            )

        # Create user
        db_user = user.create(db, obj_in=user_in)
        
        # Generate verification token and send email
        token = email_manager.create_verification_token(db_user.email)
        db_user.verification_token = token
        db_user.verification_sent_at = datetime.utcnow()
        db.commit()
        
        await email_manager.send_verification_email(db_user.email, token)
        
        return AuthResponse(
            version=api_version,
            data={
                "user": db_user,
                "message": "Registration successful. Please check your email for verification."
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorDetail(
                code="REGISTRATION_ERROR",
                message="Registration failed",
                details={"error": str(e)} if version_config.is_supported(api_version) else None
            ).dict()
        )

@router.post("/login", response_model=AuthResponse)
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    api_version: str = Depends(version_config.verify_version)
):
    """
    Login user and return tokens.
    
    Version changes:
    - 1.0: Base implementation
    - 1.1: Added refresh token
    - 2.0: Added biometric authentication option
    """
    try:
        # Check login rate limit
        await auth_rate_limiter.check_login_attempt(
            request.client.host,
            form_data.username
        )
        
        # Authenticate user
        db_user = user.get_by_email(db, email=form_data.username)
        if not db_user or not verify_password(form_data.password, db_user.hashed_password):
            await auth_rate_limiter.record_failed_attempt(
                request.client.host,
                form_data.username
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorDetail(
                    code="INVALID_CREDENTIALS",
                    message="Incorrect email or password",
                    details=None  # Don't provide details for security
                ).dict(),
                headers={"WWW-Authenticate": "Bearer"}
            )

        if not db_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorDetail(
                    code="INACTIVE_USER",
                    message="Inactive user",
                    details=None
                ).dict()
            )
            
        if not db_user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorDetail(
                    code="UNVERIFIED_EMAIL",
                    message="Email not verified",
                    details=None
                ).dict()
            )

        # Clear failed attempts on successful login
        await auth_rate_limiter.clear_attempts(
            request.client.host,
            form_data.username
        )
        
        # Update last login
        db_user.last_login = datetime.utcnow()
        db.commit()

        # Create tokens
        access_token = create_access_token(db_user.id)
        refresh_token = create_refresh_token(db_user.id)

        # Set refresh token in HTTP-only cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=30 * 24 * 60 * 60  # 30 days
        )

        return AuthResponse(
            version=api_version,
            data={
                "access_token": access_token,
                "token_type": "bearer",
                "user": db_user
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorDetail(
                code="LOGIN_ERROR",
                message="Login failed",
                details={"error": str(e)} if version_config.is_supported(api_version) else None
            ).dict()
        )

@router.post("/verify-email/{token}")
async def verify_email(
    token: str, 
    db: Session = Depends(get_db),
    api_version: str = Depends(version_config.verify_version)
):
    """Verify user's email address."""
    try:
        email = email_manager.verify_token(token, "email_verification")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorDetail(
                    code="INVALID_TOKEN",
                    message="Invalid or expired verification token",
                    details=None
                ).dict()
            )
        
        db_user = user.get_by_email(db, email=email)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorDetail(
                    code="USER_NOT_FOUND",
                    message="User not found",
                    details=None
                ).dict()
            )
        
        if db_user.is_verified:
            return AuthResponse(
                version=api_version,
                data={"message": "Email already verified"}
            )
        
        db_user.is_verified = True
        db_user.verification_token = None
        db.commit()
        
        return AuthResponse(
            version=api_version,
            data={"message": "Email verified successfully"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during email verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorDetail(
                code="VERIFICATION_ERROR",
                message="Email verification failed",
                details={"error": str(e)} if version_config.is_supported(api_version) else None
            ).dict()
        )

@router.post("/logout")
async def logout(
    response: Response,
    api_version: str = Depends(version_config.verify_version)
):
    """Logout user by clearing refresh token cookie."""
    try:
        response.delete_cookie(
            key="refresh_token",
            httponly=True,
            secure=True,
            samesite="strict"
        )
        return AuthResponse(
            version=api_version,
            data={"message": "Successfully logged out"}
        )
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorDetail(
                code="LOGOUT_ERROR",
                message="Logout failed",
                details={"error": str(e)} if version_config.is_supported(api_version) else None
            ).dict()
        )

@router.post("/refresh-token", response_model=AuthResponse)
async def refresh_token(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db),
    api_version: str = Depends(version_config.verify_version)
):
    """Get new access token using refresh token."""
    try:
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorDetail(
                    code="MISSING_TOKEN",
                    message="Refresh token missing",
                    details=None
                ).dict()
            )
        
        try:
            payload = jwt.decode(
                refresh_token,
                settings.SECRET_KEY,
                algorithms=["HS256"]
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorDetail(
                    code="INVALID_TOKEN",
                    message="Invalid refresh token",
                    details=None
                ).dict()
            )
        
        db_user = user.get(db, id=int(payload["sub"]))
        if not db_user or not db_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorDetail(
                    code="INVALID_TOKEN",
                    message="Invalid refresh token",
                    details=None
                ).dict()
            )
        
        # Create new tokens
        access_token = create_access_token(db_user.id)
        new_refresh_token = create_refresh_token(db_user.id)
        
        # Update refresh token cookie
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=30 * 24 * 60 * 60  # 30 days
        )
        
        return AuthResponse(
            version=api_version,
            data={
                "access_token": access_token,
                "token_type": "bearer",
                "user": db_user
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorDetail(
                code="REFRESH_ERROR",
                message="Token refresh failed",
                details={"error": str(e)} if version_config.is_supported(api_version) else None
            ).dict()
        )
    
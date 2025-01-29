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

router = APIRouter()

@router.post("/register", response_model=User)
async def register_user(
    request: Request,
    user_in: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user with email verification"""
    # Check registration rate limit
    await auth_rate_limiter.check_registration_rate(request.client.host)
    
    # Validate email
    if user.get_by_email(db, email=user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password
    try:
        password_check = validate_password(user_in.password)
        if not password_check.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Password does not meet requirements",
                    "suggestions": password_check.suggestions
                }
            )
    except PasswordValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e), "errors": e.errors}
        )

    # Create user
    db_user = user.create(db, obj_in=user_in)
    
    # Generate verification token and send email
    token = email_manager.create_verification_token(db_user.email)
    db_user.verification_token = token
    db_user.verification_sent_at = datetime.utcnow()
    db.commit()
    
    await email_manager.send_verification_email(db_user.email, token)
    
    return db_user

@router.post("/verify-email/{token}")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify user's email address"""
    email = email_manager.verify_token(token, "email_verification")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    db_user = user.get_by_email(db, email=email)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if db_user.is_verified:
        return {"message": "Email already verified"}
    
    db_user.is_verified = True
    db_user.verification_token = None
    db.commit()
    
    return {"message": "Email verified successfully"}

@router.post("/login", response_model=Token)
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login user and return tokens"""
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
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
        
    if not db_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified"
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

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": db_user
    }

@router.post("/forgot-password")
async def forgot_password(
    email: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Initialize password reset process"""
    # Rate limit check
    await auth_rate_limiter.check_login_attempt(request.client.host, email)
    
    db_user = user.get_by_email(db, email=email)
    if db_user and db_user.is_active:
        token = email_manager.create_password_reset_token(email)
        db_user.password_reset_token = token
        db_user.password_reset_at = datetime.utcnow()
        db.commit()
        
        await email_manager.send_password_reset_email(email, token)
    
    # Always return success to prevent email enumeration
    return {
        "message": "If an account exists with this email, "
                  "you will receive password reset instructions."
    }

@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordReset,
    db: Session = Depends(get_db)
):
    """Reset password using reset token"""
    email = email_manager.verify_token(
        reset_data.token,
        "password_reset"
    )
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    db_user = user.get_by_email(db, email=email)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    # Validate new password
    try:
        password_check = validate_password(reset_data.new_password)
        if not password_check.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Password does not meet requirements",
                    "suggestions": password_check.suggestions
                }
            )
    except PasswordValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e), "errors": e.errors}
        )
    
    # Update password
    user.update_password(db, db_user, reset_data.new_password)
    
    # Clear reset token
    db_user.password_reset_token = None
    db_user.password_reset_at = None
    db.commit()
    
    # Send notification
    await email_manager.send_password_change_notification(db_user.email)
    
    return {"message": "Password reset successful"}

@router.post("/refresh-token", response_model=Token)
async def refresh_token(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """Get new access token using refresh token"""
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing"
        )
    
    payload = jwt.decode(
        refresh_token,
        settings.SECRET_KEY,
        algorithms=["HS256"]
    )
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    db_user = user.get(db, id=int(payload["sub"]))
    if not db_user or not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
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
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": db_user
    }

@router.post("/logout")
def logout(response: Response):
    """Logout user by clearing refresh token cookie"""
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=True,
        samesite="strict"
    )
    return {"message": "Successfully logged out"}
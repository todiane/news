from datetime import datetime, timedelta
from typing import Any, Union, Optional
from passlib.context import CryptContext
from jose import jwt
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access"
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

def create_refresh_token(subject: Union[str, Any]) -> str:
    expire = datetime.utcnow() + timedelta(days=30)  # 30 days for refresh token
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh"
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

def validate_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.JWTError:
        return None

def is_token_expired(token: str) -> bool:
    payload = validate_token(token)
    if not payload:
        return True
    
    exp = payload.get("exp")
    if not exp:
        return True
        
    return datetime.utcnow() > datetime.fromtimestamp(exp)
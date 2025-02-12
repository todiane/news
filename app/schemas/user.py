from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    is_admin: Optional[bool] = False

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None

class PasswordReset(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

class Token(BaseModel):
    access_token: str
    token_type: str
    user: Optional['User'] = None

class TokenData(BaseModel):
    email: Optional[str] = None

class User(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    is_verified: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {  # Changed from schema_extra
            "example": {
                "email": "user@example.com",
                "is_active": True
            }
        }

# Avoid circular import
Token.model_rebuild()
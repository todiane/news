from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

# Base User Schema (shared properties)
class UserBase(BaseModel):
    email: EmailStr

# Schema for creating User
class UserCreate(UserBase):
    password: str

# Schema for updating User
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

# Schema for User in DB (returned to client)
class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Schema for Token
class Token(BaseModel):
    access_token: str
    token_type: str

# Schema for Token Data
class TokenData(BaseModel):
    email: Optional[str] = None
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from models import UserRole

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role_id: UserRole = UserRole.EMPLOYEE
    manager_id: Optional[int] = None
    is_active: bool = True

class UserCreate(UserBase):
    password: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class UserResponse(UserBase):
    id: int
    created_at: datetime

    # Config to allow reading from ORM models
    model_config = {"from_attributes": True}

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
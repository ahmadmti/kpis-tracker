from pydantic import BaseModel, EmailStr, field_validator, Field
from typing import Optional, List
from datetime import datetime
from models import PermissionType, MeasurementType, PeriodType

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role_id: Optional[int] = None
    is_active: bool = True

class UserCreate(UserBase):
    password: str
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class UserResponse(UserBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class RoleBase(BaseModel):
    name: str
    description: str | None = None

class RoleResponse(RoleBase):
    id: int
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# THIS IS THE MISSING PIECE
class UserOut(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True # Allows Pydantic to read SQLAlchemy models

# Recursive schema for team members
class TeamMemberOut(UserOut):
    subordinates: List["TeamMemberOut"] = []

    class Config:
        from_attributes = True

class KPIBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    target_value: float = Field(..., gt=0)
    weightage: float = Field(..., ge=0, le=100)
    measurement_type: MeasurementType
    role_id: int
    period: PeriodType = PeriodType.MONTHLY

class KPICreate(KPIBase):
    pass

class KPIOut(KPIBase):
    id: int

    class Config:
        from_attributes = True
        
class KPIOverrideCreate(BaseModel):
    user_id: int
    kpi_id: int
    custom_target_value: float = Field(..., gt=0)

class KPIOverrideOut(KPIOverrideCreate):
    id: int

    class Config:
        from_attributes = True
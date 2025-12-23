from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from database import Base

class UserRole(int, enum.Enum):
    ADMIN = 1
    MANAGER = 2
    EMPLOYEE = 3

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    
    # Storing Enum as Integer for role_id
    role_id = Column(Integer, nullable=False, default=UserRole.EMPLOYEE.value)
    
    # Self-referential foreign key for manager
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    manager = relationship("User", remote_side=[id], backref="subordinates")
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from database import Base

class PermissionType(str, enum.Enum):
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    SYSTEM_CONFIG = "system:config"

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    permissions = relationship("RolePermission", back_populates="role")

class RolePermission(Base):
    __tablename__ = "role_permissions"
    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    permission_name = Column(String, nullable=False)
    role = relationship("Role", back_populates="permissions")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True) # Changed to nullable for bootstrap
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    manager = relationship("User", remote_side=[id], backref="subordinates")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Hierarchy Field
    # Relationships

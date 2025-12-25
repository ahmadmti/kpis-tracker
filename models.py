from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from database import Base
from datetime import datetime, timezone

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

class MeasurementType(str, enum.Enum):
    COUNT = "COUNT"
    AMOUNT = "AMOUNT"
    PERCENTAGE = "PERCENTAGE"

class PeriodType(str, enum.Enum):
    MONTHLY = "MONTHLY"

class KPI(Base):
    __tablename__ = "kpis"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    category = Column(String, nullable=False)
    target_value = Column(Float, nullable=False) # Must be > 0
    weightage = Column(Float, nullable=False)    # 0 to 100
    measurement_type = Column(Enum(MeasurementType), nullable=False)
    period = Column(Enum(PeriodType), default=PeriodType.MONTHLY)
    
    # Links KPI to a specific Role
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)

class KPIOverride(Base):
    __tablename__ = "kpi_overrides"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    kpi_id = Column(Integer, ForeignKey("kpis.id"), nullable=False)
    custom_target_value = Column(Float, nullable=False) # The new override value
    
    # Relationships for easy lookup
    user = relationship("User", backref="overrides")
    kpi = relationship("KPI")

class AchievementStatus(str, enum.Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"

class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    kpi_id = Column(Integer, ForeignKey("kpis.id"), nullable=False)
    verifier_id = Column(Integer, ForeignKey("users.id"), nullable=True) # <--- Must be above the relationship
    achieved_value = Column(Float, nullable=False) # Must be >= 0
    description = Column(String)
    evidence_url = Column(String) # URL to proof
    achievement_date = Column(DateTime, default=datetime.now(timezone.utc))
    status = Column(Enum(AchievementStatus), default=AchievementStatus.PENDING)

    # Relationships
    user = relationship("User", foreign_keys="[Achievement.user_id]", backref="my_achievements")
    verifier = relationship("User", foreign_keys="[Achievement.verifier_id]", backref="verified_achievements")
    #user = relationship("User")
    kpi = relationship("KPI")
    verifier_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    rejection_reason = Column(String, nullable=True)

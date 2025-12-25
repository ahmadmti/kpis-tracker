from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Optional, List
from database import engine, Base, get_db
import models, schemas, auth
from datetime import datetime


Base.metadata.create_all(bind=engine)

app = FastAPI(title="KPIs Tracker")
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with your specific IP
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/bootstrap")
def bootstrap_system(db: Session = Depends(get_db)):
    """Sets up the initial Admin role and permissions"""
    # Check if Admin already exists
    if db.query(models.Role).filter(models.Role.name == "Admin").first():
        return {"message": "Already bootstrapped"}
    
    # Create the Admin Role
    admin_role = models.Role(name="Admin", description="Full Access")
    db.add(admin_role)
    db.commit()
    db.refresh(admin_role)
    
    # Link all permissions to this Admin role
    for perm in models.PermissionType:
        new_p = models.RolePermission(role_id=admin_role.id, permission_name=perm.value)
        db.add(new_p)
    db.commit()
    return {"message": "Admin role and permissions created successfully!"}

# Permission Helper
def check_permission(required_perm: models.PermissionType):
    def permission_checker(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
        has_perm = db.query(models.RolePermission).filter(
            models.RolePermission.role_id == current_user.role_id,
            models.RolePermission.permission_name == required_perm.value
        ).first()
        if not has_perm:
            raise HTTPException(status_code=403, detail="Forbidden")
        return current_user
    return permission_checker


@app.post("/token", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email exists")
    new_user = models.User(
        email=user.email,
        full_name=user.full_name,
        password_hash=auth.get_password_hash(user.password),
        role_id=user.role_id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/health")
def health():
    return {"status": "online"}

@app.get("/users/", response_model=list[schemas.UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Admin Only: List all registered users"""
    # Check if the requester is an Admin (Module 3 Logic)
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="Not enough permissions")
        
    return db.query(models.User).all()

def check_circular_reference(db: Session, user_id: int, proposed_manager_id: int):
    """Senior Logic: Ensure the manager is not a subordinate of the user."""
    if user_id == proposed_manager_id:
        raise HTTPException(status_code=400, detail="User cannot manage themselves.")
    
    current_m_id = proposed_manager_id
    while current_m_id is not None:
        if current_m_id == user_id:
            raise HTTPException(status_code=400, detail="Circular reporting detected.")
        
        # Move up the chain
        manager = db.query(models.User).filter(models.User.id == current_m_id).first()
        current_m_id = manager.manager_id if manager else None

@app.get("/users/{user_id}/team", response_model=schemas.TeamMemberOut)
def get_user_team(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Fetch the entire hierarchy starting from a specific user."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/users/{user_id}/manager")
def update_manager(
    user_id: int, 
    manager_id: Optional[int], 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Safely update a user's manager with circular reporting protection."""
    if current_user.role_id != 1: # Admin only
        raise HTTPException(status_code=403, detail="Only admins can change hierarchy")
        
    if manager_id:
        check_circular_reference(db, user_id, manager_id)
        
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    db_user.manager_id = manager_id
    db.commit()
    return {"message": "Hierarchy updated successfully"}

@app.post("/kpis/", response_model=schemas.KPIOut)
def create_kpi(
    kpi: schemas.KPICreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Only Admin can define KPIs
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="Forbidden: Insufficient permissions")

    # Business Rule: Total weightage per role/period <= 100
    current_weight_sum = db.query(func.sum(models.KPI.weightage)).filter(
        models.KPI.role_id == kpi.role_id,
        models.KPI.period == kpi.period
    ).scalar() or 0.0

    if current_weight_sum + kpi.weightage > 100:
        raise HTTPException(
            status_code=400, 
            detail=f"Total weightage for this role/period exceeds 100. (Current: {current_weight_sum})"
        )

    db_kpi = models.KPI(**kpi.dict())
    db.add(db_kpi)
    db.commit()
    db.refresh(db_kpi)
    
    # Audit Log (Passive)
    # log_action(db, current_user.id, "KPI_CREATED", f"Created KPI {db_kpi.id}")
    
    return db_kpi

@app.post("/kpis/overrides/", response_model=schemas.KPIOverrideOut)
def create_kpi_override(
    override: schemas.KPIOverrideCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Senior Logic: Admins can set custom targets for specific users."""
    # 1. Permission Check
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="Admin access required")

    # 2. Prevent duplicates (Update existing if found)
    existing = db.query(models.KPIOverride).filter(
        models.KPIOverride.user_id == override.user_id,
        models.KPIOverride.kpi_id == override.kpi_id
    ).first()

    if existing:
        existing.custom_target_value = override.custom_target_value
        db.commit()
        db.refresh(existing)
        return existing

    # 3. Create new override
    db_override = models.KPIOverride(**override.model_dump())
    db.add(db_override)
    db.commit()
    db.refresh(db_override)
    return db_override

@app.post("/achievements/", response_model=schemas.AchievementOut)
def log_achievement(
    achievement: schemas.AchievementCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Senior Logic: Log KPI progress with current-period validation."""
    
    # 1. Period Validation: Ensure achievement_date is within current month/year
    now = datetime.utcnow()
    if achievement.achievement_date.month != now.month or \
       achievement.achievement_date.year != now.year:
        raise HTTPException(
            status_code=400, 
            detail="Achievements must be logged within the current month/period."
        )

    # 2. Verify KPI exists
    kpi_exists = db.query(models.KPI).filter(models.KPI.id == achievement.kpi_id).first()
    if not kpi_exists:
        raise HTTPException(status_code=404, detail="KPI ID not found.")

    # 3. Save Entry (Status defaults to PENDING)
    db_achievement = models.Achievement(
        **achievement.model_dump(),
        user_id=current_user.id
    )
    
    db.add(db_achievement)
    db.commit()
    db.refresh(db_achievement)
    return db_achievement
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, extract
from sqlalchemy.orm import Session
from typing import Optional, List
from database import engine, Base, get_db
import models, schemas, auth
from datetime import datetime, timezone, timedelta
import services
import audit, automation
from fastapi.responses import Response
import reports
import secrets
import uuid

# Create all tables - this will handle new columns/enums automatically
# Note: For enum changes, existing databases may need manual update
# But this ensures new installations work correctly
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    # Log but don't fail - tables might already exist
    print(f"Note: Database initialization: {e}")

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
    audit.log_action(
        db, user_id=user.id, action=models.ActionType.LOGIN, 
        entity=models.EntityType.USER, entity_id=user.id, 
        description="User logged in successfully"
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=schemas.UserResponse)
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        auth.check_permission(models.PermissionType.USER_CREATE)
    )
):

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
    current_user: models.User = Depends(auth.check_permission(models.PermissionType.SYSTEM_CONFIG))

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

    # Handle both Pydantic v1 and v2
    try:
        kpi_data = kpi.model_dump() if hasattr(kpi, 'model_dump') else kpi.dict()
    except:
        kpi_data = kpi.dict()
    db_kpi = models.KPI(**kpi_data)
    db.add(db_kpi)
    db.commit()
    db.refresh(db_kpi)
    
    # Audit Log (Passive)
    # log_action(db, current_user.id, "KPI_CREATED", f"Created KPI {db_kpi.id}")
    audit.log_action(
        db, user_id=current_user.id, action=models.ActionType.CREATE, 
        entity=models.EntityType.KPI, entity_id=db_kpi.id, 
        description=f"Created KPI: {db_kpi.name}"
    )
    return db_kpi

@app.post("/kpis/overrides/", response_model=schemas.KPIOverrideOut)
def create_kpi_override(
    override: schemas.KPIOverrideCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.check_permission(models.PermissionType.SYSTEM_CONFIG))

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
    # Handle both Pydantic v1 and v2
    try:
        achievement_data = achievement.model_dump() if hasattr(achievement, 'model_dump') else achievement.dict()
    except:
        achievement_data = achievement.dict()
    
    db_achievement = models.Achievement(
        **achievement_data,
        user_id=current_user.id
    )
    
    db.add(db_achievement)
    db.commit()
    db.refresh(db_achievement)
    audit.log_action(
        db, user_id=current_user.id, action=models.ActionType.CREATE, 
        entity=models.EntityType.ACHIEVEMENT, entity_id=db_achievement.id, 
        description=f"Submitted achievement for KPI {db_achievement.kpi_id}"
    )
    return db_achievement

@app.put("/achievements/{achievement_id}/verify")
def verify_achievement(
    achievement_id: int,
    data: schemas.AchievementVerify,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.check_permission(models.PermissionType.USER_READ))

):
    """Senior Logic: Managerial verification with state-transition enforcement."""
    # 1. Fetch Achievement
    achievement = db.query(models.Achievement).filter(models.Achievement.id == achievement_id).first()
    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")

    # 2. Strict State Check: Must be PENDING
    if achievement.status != models.AchievementStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Cannot change status of a {achievement.status} entry")

    # 3. Hierarchy Check: Is the verifier the Admin OR the user's manager?
    user_to_verify = db.query(models.User).filter(models.User.id == achievement.user_id).first()
    is_manager = user_to_verify.manager_id == current_user.id
    is_admin = current_user.role_id == 1

    if not (is_admin or is_manager):
        raise HTTPException(status_code=403, detail="Only managers or admins can verify achievements")

    # 4. Apply Changes
    achievement.status = data.status
    achievement.verifier_id = current_user.id
    achievement.verified_at = datetime.now(timezone.utc)    
    if data.status == models.AchievementStatus.REJECTED:
        if not data.rejection_reason:
            raise HTTPException(status_code=400, detail="Rejection reason required")
        achievement.rejection_reason = data.rejection_reason

    db.commit()
    audit.log_action(
        db, 
        user_id=current_user.id, 
        action=models.ActionType.VERIFY, 
        entity=models.EntityType.ACHIEVEMENT,
        entity_id=achievement.id,
        description=f"Achievement {data.status} for user {achievement.user_id}"
    )
    return {"message": f"Achievement successfully {data.status}"}

@app.get("/users/{user_id}/score")
def get_user_monthly_score(
    user_id: int,
    month: int = datetime.now().month,
    year: int = datetime.now().year,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Senior Logic: Only Admin, Manager, or the User themselves can see the score."""
    is_admin = current_user.role_id == 1
    is_owner = current_user.id == user_id
    
    user_to_check = db.query(models.User).filter(models.User.id == user_id).first()
    is_manager = user_to_check.manager_id == current_user.id if user_to_check else False

    if not (is_admin or is_owner or is_manager):
        raise HTTPException(status_code=403, detail="Not authorized to view this score")

    score = services.calculate_user_kpi_score(db, user_id, month, year)
    return {
        "user_id": user_id,
        "period": f"{year}-{month:02d}",
        "total_weighted_score": score
    }

@app.post("/admin/evaluate/{user_id}")
def run_evaluation(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.check_permission(models.PermissionType.SYSTEM_CONFIG))

):
    """Senior Logic: Admin-triggered performance evaluation."""
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    now = datetime.now(timezone.utc)
    recommendation = automation.evaluate_performance(db, user_id, now.month, now.year)
    
    if not recommendation:
        return {"message": "Evaluation complete: Performance is within normal range. No action recommended."}
    
    # Audit the recommendation generation
    audit.log_action(
        db, user_id=current_user.id, action=models.ActionType.CREATE,
        entity=models.EntityType.USER, entity_id=user_id,
        description=f"Generated {recommendation.recommendation} recommendation for user {user_id}"
    )
    
    return recommendation

@app.get("/admin/recommendations")
def get_all_recommendations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.check_permission(models.PermissionType.SYSTEM_CONFIG))

):
    """View all automated performance flags."""
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return db.query(models.AutomationRule).all()

@app.get("/users/me", response_model=schemas.User)
def get_current_user_profile(current_user: models.User = Depends(auth.get_current_user)):
    """Senior Logic: Returns the logged-in user's profile info."""
    return current_user

@app.get("/reports/export")
def export_report(
    format: str = "excel", # or "pdf"
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Senior Logic: Export performance data based on role permissions."""
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="Admin access required")

    # 1. Gather Data (Similar to Dashboard logic)
    all_users = db.query(models.User).all()
    report_data = []
    now = datetime.now(timezone.utc)

    for user in all_users:
        score = services.calculate_user_kpi_score(db, user.id, now.month, now.year)
        report_data.append({
            "user_id": user.id,
            "full_name": user.full_name,
            "score": score,
            "period": f"{now.year}-{now.month}"
        })

    # 2. Generate File
    if format == "excel":
        file_content = reports.generate_excel_report(report_data)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = "kpi_report.xlsx"
    else:
        file_content = reports.generate_pdf_report(report_data)
        media_type = "application/pdf"
        filename = "kpi_report.pdf"

    # 3. Audit the Export
    audit.log_action(
        db, user_id=current_user.id, action=models.ActionType.CREATE,
        entity=models.EntityType.USER, description=f"Exported {format} report"
    )

    return Response(
        content=file_content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/roles")
def get_roles(db: Session = Depends(get_db)):
    return db.query(models.Role).all()

@app.get("/permissions")
def get_permissions():
    return [{"key": p.value} for p in models.PermissionType]

@app.get("/roles/{role_id}/permissions")
def get_role_permissions(role_id: int, db: Session = Depends(get_db)):
    perms = db.query(models.RolePermission).filter(
        models.RolePermission.role_id == role_id
    ).all()
    return [p.permission_name for p in perms]
@app.put("/roles/{role_id}/permissions")
def update_role_permissions(
    role_id: int,
    permissions: list[str],
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.role_id != 1:
        raise HTTPException(status_code=403)

    # Protect Admin role (id = 1)
    if role_id == 1:
        protected = {
            models.PermissionType.USER_READ.value,
            models.PermissionType.SYSTEM_CONFIG.value
        }
    else:
        protected = set()

    db.query(models.RolePermission).filter(
        models.RolePermission.role_id == role_id,
        ~models.RolePermission.permission_name.in_(protected)
    ).delete()


    for perm in permissions:
        db.add(models.RolePermission(
            role_id=role_id,
            permission_name=perm
        ))
        

    db.commit()
    return {"status": "updated"}

# ==================== PASSWORD MANAGEMENT ====================

@app.post("/auth/forgot-password")
def forgot_password(request: schemas.ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Generate password reset token and send email (simplified - just returns token for now)"""
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if not user:
        # Don't reveal if email exists
        return {"message": "If the email exists, a password reset link has been sent."}
    
    # Generate secure token
    reset_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    # Invalidate old tokens
    db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.user_id == user.id,
        models.PasswordResetToken.used == False
    ).update({"used": True})
    
    # Create new token
    db_token = models.PasswordResetToken(
        user_id=user.id,
        token=reset_token,
        expires_at=expires_at
    )
    db.add(db_token)
    db.commit()
    
    # In production, send email with reset link
    # For now, return token (in production, this should be sent via email)
    return {"message": "Password reset token generated", "token": reset_token}

@app.post("/auth/reset-password")
def reset_password(request: schemas.ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using token"""
    token_record = db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.token == request.token,
        models.PasswordResetToken.used == False,
        models.PasswordResetToken.expires_at > datetime.now(timezone.utc)
    ).first()
    
    if not token_record:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    # Update password
    user = db.query(models.User).filter(models.User.id == token_record.user_id).first()
    user.password_hash = auth.get_password_hash(request.new_password)
    token_record.used = True
    db.commit()
    
    audit.log_action(
        db, user_id=user.id, action=models.ActionType.UPDATE,
        entity=models.EntityType.USER, entity_id=user.id,
        description="Password reset via forgot password"
    )
    
    return {"message": "Password reset successfully"}

@app.post("/auth/change-password")
def change_password(
    request: schemas.ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Change password for logged-in user"""
    if not auth.verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    current_user.password_hash = auth.get_password_hash(request.new_password)
    db.commit()
    
    audit.log_action(
        db, user_id=current_user.id, action=models.ActionType.UPDATE,
        entity=models.EntityType.USER, entity_id=current_user.id,
        description="Password changed"
    )
    
    return {"message": "Password changed successfully"}

# ==================== DASHBOARD ENDPOINTS ====================

@app.get("/dashboard/admin")
def admin_dashboard(
    month: Optional[int] = None,
    year: Optional[int] = None,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Admin dashboard with filtering by date and user"""
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    now = datetime.now(timezone.utc)
    filter_month = month or now.month
    filter_year = year or now.year
    
    # Get users to display
    if user_id:
        users = db.query(models.User).filter(models.User.id == user_id).all()
    else:
        users = db.query(models.User).all()
    
    dashboard_data = []
    for user in users:
        score = services.calculate_user_kpi_score(db, user.id, filter_month, filter_year)
        
        # Get achievements for this user/period
        achievements = db.query(models.Achievement).filter(
            models.Achievement.user_id == user.id,
            extract('month', models.Achievement.achievement_date) == filter_month,
            extract('year', models.Achievement.achievement_date) == filter_year
        ).all()
        
        achievement_list = [{
            "id": a.id,
            "kpi_id": a.kpi_id,
            "achieved_value": a.achieved_value,
            "status": a.status.value,
            "description": a.description,
            "achievement_date": a.achievement_date.isoformat() if a.achievement_date else None
        } for a in achievements]
        
        dashboard_data.append({
            "user_id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "total_weighted_score": score,
            "period": f"{filter_year}-{filter_month:02d}",
            "achievements": achievement_list
        })
    
    return {
        "user_scores": dashboard_data,
        "total_users": len(users),
        "period": f"{filter_year}-{filter_month:02d}"
    }

@app.get("/dashboard/manager")
def manager_dashboard(
    month: Optional[int] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Manager dashboard - own + team performance"""
    now = datetime.now(timezone.utc)
    filter_month = month or now.month
    filter_year = year or now.year
    
    # Get manager's own score
    own_score = services.calculate_user_kpi_score(db, current_user.id, filter_month, filter_year)
    
    # Get team members (direct subordinates)
    team_members = db.query(models.User).filter(
        models.User.manager_id == current_user.id
    ).all()
    
    team_data = []
    for member in team_members:
        score = services.calculate_user_kpi_score(db, member.id, filter_month, filter_year)
        team_data.append({
            "user_id": member.id,
            "full_name": member.full_name,
            "email": member.email,
            "total_weighted_score": score,
            "period": f"{filter_year}-{filter_month:02d}"
        })
    
    return {
        "manager": {
            "user_id": current_user.id,
            "full_name": current_user.full_name,
            "email": current_user.email,
            "total_weighted_score": own_score,
            "period": f"{filter_year}-{filter_month:02d}"
        },
        "team": team_data,
        "period": f"{filter_year}-{filter_month:02d}"
    }

@app.get("/dashboard/sdr")
def sdr_dashboard(
    month: Optional[int] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """SDR dashboard - own performance"""
    now = datetime.now(timezone.utc)
    filter_month = month or now.month
    filter_year = year or now.year
    
    score = services.calculate_user_kpi_score(db, current_user.id, filter_month, filter_year)
    
    # Get user's KPIs
    role_kpis = db.query(models.KPI).filter(models.KPI.role_id == current_user.role_id).all()
    
    # Get achievements
    achievements = db.query(models.Achievement).filter(
        models.Achievement.user_id == current_user.id,
        extract('month', models.Achievement.achievement_date) == filter_month,
        extract('year', models.Achievement.achievement_date) == filter_year
    ).all()
    
    kpi_details = []
    for kpi in role_kpis:
        # Check for override
        override = db.query(models.KPIOverride).filter(
            models.KPIOverride.user_id == current_user.id,
            models.KPIOverride.kpi_id == kpi.id
        ).first()
        target = override.custom_target_value if override else kpi.target_value
        
        # Get verified achievements for this KPI
        kpi_achievements = [a for a in achievements if a.kpi_id == kpi.id and a.status == models.AchievementStatus.VERIFIED]
        achieved_sum = sum(a.achieved_value for a in kpi_achievements)
        
        kpi_details.append({
            "kpi_id": kpi.id,
            "name": kpi.name,
            "target_value": target,
            "achieved_value": achieved_sum,
            "weightage": kpi.weightage,
            "frequency": kpi.period.value if kpi.period else "MONTHLY",
            "status": "completed" if achieved_sum >= target else "in_progress"
        })
    
    return {
        "user_id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "total_weighted_score": score,
        "period": f"{filter_year}-{filter_month:02d}",
        "kpis": kpi_details,
        "achievements": [{
            "id": a.id,
            "kpi_id": a.kpi_id,
            "achieved_value": a.achieved_value,
            "status": a.status.value,
            "description": a.description
        } for a in achievements]
    }

@app.get("/kpis/")
def list_kpis(
    role_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """List KPIs, optionally filtered by role"""
    query = db.query(models.KPI)
    if role_id:
        query = query.filter(models.KPI.role_id == role_id)
    
    kpis = query.all()
    
    # Convert to dict format with backward compatibility
    result = []
    for k in kpis:
        # Handle period - might be None or old enum value
        period_value = None
        if k.period:
            if hasattr(k.period, 'value'):
                period_value = k.period.value
            else:
                period_value = str(k.period)
        
        # Default to MONTHLY if period is missing (backward compatibility)
        if not period_value:
            period_value = "MONTHLY"
        
        result.append({
            "id": k.id,
            "name": k.name,
            "description": k.description,
            "category": k.category,
            "target_value": k.target_value,
            "weightage": k.weightage,
            "measurement_type": k.measurement_type.value if k.measurement_type else None,
            "role_id": k.role_id,
            "period": period_value
        })
    return result

@app.get("/achievements/")
def list_achievements(
    user_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """List achievements with optional filters"""
    query = db.query(models.Achievement)
    
    # Role-based filtering
    if current_user.role_id == 1:  # Admin sees all
        if user_id:
            query = query.filter(models.Achievement.user_id == user_id)
    elif current_user.role_id == 2:  # Manager sees own + team
        team_user_ids = [u.id for u in db.query(models.User).filter(
            models.User.manager_id == current_user.id
        ).all()]
        team_user_ids.append(current_user.id)
        query = query.filter(models.Achievement.user_id.in_(team_user_ids))
    else:  # SDR sees only own
        query = query.filter(models.Achievement.user_id == current_user.id)
    
    if status_filter:
        try:
            status_enum = models.AchievementStatus(status_filter)
            query = query.filter(models.Achievement.status == status_enum)
        except ValueError:
            pass  # Invalid status, ignore filter
    
    achievements = query.all()
    
    # Convert to dict format
    return [{
        "id": a.id,
        "user_id": a.user_id,
        "kpi_id": a.kpi_id,
        "achieved_value": a.achieved_value,
        "description": a.description,
        "evidence_url": a.evidence_url,
        "achievement_date": a.achievement_date.isoformat() if a.achievement_date else None,
        "status": a.status.value if a.status else None,
        "verifier_id": a.verifier_id,
        "verified_at": a.verified_at.isoformat() if a.verified_at else None,
        "rejection_reason": a.rejection_reason
    } for a in achievements]



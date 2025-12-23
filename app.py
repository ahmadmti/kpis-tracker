from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import engine, Base, get_db
import models, schemas, auth

Base.metadata.create_all(bind=engine)

app = FastAPI(title="KPIs Tracker")

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
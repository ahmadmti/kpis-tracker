from sqlalchemy.orm import Session
from sqlalchemy import func
import models

def calculate_user_kpi_score(db: Session, user_id: int, month: int, year: int):
    """
    Senior Logic: Aggregates VERIFIED achievements vs Targets.
    Calculates weighted score, capped at 100% per KPI.
    """
    # 1. Get all KPIs assigned to the user's role
    user = db.query(models.User).filter(models.User.id == user_id).first()
    role_kpis = db.query(models.KPI).filter(models.KPI.role_id == user.role_id).all()
    
    total_performance_score = 0.0

    for kpi in role_kpis:
        # 2. Check for User-Specific Overrides
        override = db.query(models.KPIOverride).filter(
            models.KPIOverride.user_id == user_id,
            models.KPIOverride.kpi_id == kpi.id
        ).first()
        
        target = override.custom_target_value if override else kpi.target_value

        # 3. Sum only VERIFIED achievements for this KPI in the given month/year
        actual_sum = db.query(func.sum(models.Achievement.achieved_value)).filter(
            models.Achievement.user_id == user_id,
            models.Achievement.kpi_id == kpi.id,
            models.Achievement.status == models.AchievementStatus.VERIFIED,
            func.extract('month', models.Achievement.achievement_date) == month,
            func.extract('year', models.Achievement.achievement_date) == year
        ).scalar() or 0.0

        # 4. Calculation: (Actual / Target) * Weightage
        completion_pct = (actual_sum / target) if target > 0 else 0
        
        # Requirement: Cap completion percentage at 1.0 (100%)
        if completion_pct > 1.0:
            completion_pct = 1.0
            
        kpi_score = completion_pct * kpi.weightage
        total_performance_score += kpi_score

    return round(total_performance_score, 2)
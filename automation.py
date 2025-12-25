from sqlalchemy.orm import Session
import models
import services
from datetime import datetime, timezone

def evaluate_performance(db: Session, user_id: int, month: int, year: int):
    """
    Senior Logic: Evaluates score against corporate thresholds.
    Thresholds:
    - 95%+: Bonus/Promotion
    - 70-94%: Satisfactory (No recommendation)
    - 50-69%: Warning
    - <50%: Final Warning / Termination
    """
    score = services.calculate_user_kpi_score(db, user_id, month, year)
    period_str = f"{year}-{month:02d}"
    
    rec_type = None
    if score >= 95:
        rec_type = models.RecommendationType.BONUS
    elif 50 <= score < 70:
        rec_type = models.RecommendationType.WARNING
    elif score < 50:
        rec_type = models.RecommendationType.FINAL_WARNING

    if rec_type:
        new_rec = models.AutomationRule(
            user_id=user_id,
            score_achieved=score,
            recommendation=rec_type,
            period=period_str
        )
        db.add(new_rec)
        db.commit()
        return new_rec
    return None
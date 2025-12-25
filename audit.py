from sqlalchemy.orm import Session
import models
from datetime import datetime, timezone

def log_action(
    db: Session, 
    user_id: int, 
    action: models.ActionType, 
    entity: models.EntityType, 
    entity_id: int = None, 
    description: str = "",
    meta: dict = None
):
    """Senior Utility: Passive, write-only logging."""
    try:
        new_log = models.AuditLog(
            user_id=user_id,
            action_type=action,
            entity_type=entity,
            entity_id=entity_id,
            description=description,
            metadata_json=meta
        )
        db.add(new_log)
        db.commit() # We commit immediately to ensure the log is saved
    except Exception as e:
        # In production, we log this to a file so the main app doesn't crash
        print(f"Audit Log Failed: {e}")
        db.rollback()
from typing import Optional
from sqlmodel import Session, select
from app.src.config.database import Meal

def fetch_latest_meal_for_one(db: Session, facility_id: int) -> Optional[Meal]:
    stmt = (
        select(Meal)
        .where(Meal.facility_id == facility_id)
        .order_by(Meal.timestamp.desc())
        .limit(1)
    )
    return db.exec(stmt).first()

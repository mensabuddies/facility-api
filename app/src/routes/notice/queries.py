from typing import Optional
from sqlmodel import Session, select
from app.src.config.database import Notice

def fetch_latest_notice_for_one(db: Session, facility_id: int) -> Optional[Notice]:
    stmt = (
        select(Notice)
        .where(Notice.facility_id == facility_id)
        .order_by(Notice.timestamp.desc())
        .limit(1)
    )
    return db.exec(stmt).first()

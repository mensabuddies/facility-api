from typing import Iterable

from sqlalchemy import func, and_
from sqlmodel import Session, select

from app.src.config.database import OpeningHour


def fetch_latest_opening_hours_for(db: Session, facility_ids: Iterable[int]) -> dict[int, dict]:
    """Return {facility_id: opening_hours_json} for the latest timestamp per facility."""
    fac_ids = list(facility_ids)
    if not fac_ids:
        return {}

    latest_ts_subq = (
        select(
            OpeningHour.facility_id,
            func.max(OpeningHour.timestamp).label("ts"),
        )
        .where(OpeningHour.facility_id.in_(fac_ids))
        .group_by(OpeningHour.facility_id)
        .subquery()
    )

    rows = db.exec(
        select(OpeningHour).join(
            latest_ts_subq,
            and_(
                OpeningHour.facility_id == latest_ts_subq.c.facility_id,
                OpeningHour.timestamp == latest_ts_subq.c.ts,
            ),
        )
    ).all()

    return {row.facility_id: row.opening_hours for row in rows}

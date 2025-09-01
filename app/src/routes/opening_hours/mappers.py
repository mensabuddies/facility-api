# mappers.py
from typing import Optional

from app.src.routes.opening_hours.schemas import OpeningHoursOutput, OpeningHoursPerDay


def map_opening_hours(oh_json: Optional[dict]) -> Optional[OpeningHoursOutput]:
    if not isinstance(oh_json, dict):
        return None
    # Each day may be absent → keep None; present → validate via Pydantic
    def per(day: str):
        data = oh_json.get(day)
        return OpeningHoursPerDay(**data) if isinstance(data, dict) else None

    return OpeningHoursOutput(
        monday=per("monday"),
        tuesday=per("tuesday"),
        wednesday=per("wednesday"),
        thursday=per("thursday"),
        friday=per("friday"),
        saturday=per("saturday"),
        sunday=per("sunday"),
    )

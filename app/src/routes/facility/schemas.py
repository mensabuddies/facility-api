from pydantic import BaseModel

from app.src.routes.location.schemas import LocationOut
from app.src.routes.opening_hours.schemas import OpeningHoursOutput


class FacilityTypeOut(BaseModel):
    id: int
    name: str


class FacilityOut(BaseModel):
    id: int
    name: str
    address: str
    description: str
    uuid: str
    organization_id: int
    location: LocationOut | None = None
    facility_type: FacilityTypeOut | None = None
    opening_hours: OpeningHoursOutput | None = None

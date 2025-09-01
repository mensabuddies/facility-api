from app.src.config.database import Facility
from app.src.routes.facility.schemas import FacilityOut, FacilityTypeOut
from app.src.routes.location.schemas import LocationOut
from app.src.routes.opening_hours.mappers import map_opening_hours


def map_facility(
    f: Facility,
    opening_hours_json_by_id: dict[int, dict],
) -> FacilityOut:
    return FacilityOut(
        id=f.id,
        name=f.name,
        address=f.address,
        description=f.description,
        uuid=f.uuid,
        organization_id=f.organization_id,
        location=(
            LocationOut(id=f.location.id, name=f.location.name)
            if f.location else None
        ),
        facility_type=(
            FacilityTypeOut(id=f.facility_type.id, name=f.facility_type.name)
            if f.facility_type else None
        ),
        opening_hours=map_opening_hours(opening_hours_json_by_id.get(f.id)),
    )

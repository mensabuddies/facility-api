from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.src.config.database import get_session, Facility
from app.src.routes.facility.queries import fetch_facility_by_uuid, fetch_facility_by_id
from app.src.routes.facility.schemas import FacilityOut
from app.src.routes.opening_hours.queries import fetch_latest_opening_hours_for
from app.src.routes.organization.mappers import map_facility

router = APIRouter(prefix="/facility",
                   tags=["Facility"])


@router.get("/uuid/{facility_uuid}",
            response_model=FacilityOut)
async def get_facility_by_uuid(facility_uuid: str, db: Session = Depends(get_session)):
    facility: Facility = fetch_facility_by_uuid(uuid=facility_uuid, db=db)

    latest_oh = fetch_latest_opening_hours_for(db, [facility.id])
    return map_facility(facility, latest_oh)


@router.get("/id/{facility_id}",
            response_model=FacilityOut)
async def get_facility_by_id(facility_id: int, db: Session = Depends(get_session)):
    facility: Facility = fetch_facility_by_id(facility_id=facility_id, db=db)

    latest_oh = fetch_latest_opening_hours_for(db, [facility.id])
    return map_facility(facility, latest_oh)

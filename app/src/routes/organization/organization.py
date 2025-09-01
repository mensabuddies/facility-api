from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.src.config.database import get_session, Organization, Location, Facility
from app.src.routes.facility.queries import fetch_facilities
from app.src.routes.facility.schemas import FacilityOut
from app.src.routes.opening_hours.queries import fetch_latest_opening_hours_for
from app.src.routes.organization.mappers import map_facility

router = APIRouter(prefix="/organization",
                   tags=["Organization"])


@router.get("",
            response_model=List[Organization])
async def get_organizations(db: Session = Depends(get_session)):
    organizations: List[Organization] = db.exec(select(Organization)).all()
    return organizations


@router.get("/{organization_id}/locations",
            response_model=List[Location])
async def get_locations_for_organization(organization_id: int, db: Session = Depends(get_session)):
    locations = db.exec(select(Location)
                        .join(Facility)  # Location → Facility
                        .where(Facility.organization_id == organization_id)
                        .distinct()).all()
    return locations


@router.get("/{organization_id}/facilities", response_model=List[FacilityOut])
async def get_facilities_for_organization(organization_id: int,
                                          location_id: Optional[int] = None,
                                          type_id: Optional[int] = None,
                                          db: Session = Depends(get_session)):
    facilities: list[Facility] = fetch_facilities(db=db,
                                                  organization_id=organization_id,
                                                  location_id=location_id,
                                                  type_id=type_id)
    if not facilities:
        return []

    latest_oh = fetch_latest_opening_hours_for(db, (f.id for f in facilities))
    return [map_facility(f, latest_oh) for f in facilities]

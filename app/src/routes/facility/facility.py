from http import HTTPStatus
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.src.config.database import get_session, Facility
from app.src.routes.facility.file_response import serve_image_by_uuid, serve_image_by_id
from app.src.routes.facility.queries import fetch_facility_by_uuid, fetch_facility_by_id
from app.src.routes.facility.schemas import FacilityOut
from app.src.routes.meal.mappers import map_meal
from app.src.routes.meal.queries import fetch_latest_meal_for_one
from app.src.routes.meal.schemas import MealOut
from app.src.routes.notice.mappers import map_notice
from app.src.routes.notice.queries import fetch_latest_notice_for_one
from app.src.routes.notice.schemas import NoticeOut
from app.src.routes.opening_hours.mappers import map_opening_hours
from app.src.routes.opening_hours.queries import fetch_latest_opening_hours_for
from app.src.routes.opening_hours.schemas import OpeningHoursOutput
from app.src.routes.organization.mappers import map_facility

IMAGES_DIR = Path(__file__).resolve().parents[4] / "assets" / "images"

router = APIRouter(prefix="/facility",
                   tags=["Facility"])


@router.get("/uuid/{facility_uuid}",
            response_model=FacilityOut)
async def get_facility_by_uuid(facility_uuid: UUID, db: Session = Depends(get_session)):
    facility: Facility = fetch_facility_by_uuid(uuid=facility_uuid, db=db)

    latest_oh = fetch_latest_opening_hours_for(db, [facility.id])
    return map_facility(facility, latest_oh)


@router.get("/id/{facility_id}",
            response_model=FacilityOut)
async def get_facility_by_id(facility_id: int, db: Session = Depends(get_session)):
    facility: Facility = fetch_facility_by_id(facility_id=facility_id, db=db)

    latest_oh = fetch_latest_opening_hours_for(db, [facility.id])
    return map_facility(facility, latest_oh)


@router.get("/id/{facility_id}/opening_hours",
            response_model=OpeningHoursOutput)
async def get_opening_hours(facility_id: int, db: Session = Depends(get_session)):
    latest_map = fetch_latest_opening_hours_for(db, [facility_id])  # {id: json}
    oh_json = latest_map.get(facility_id)
    return map_opening_hours(oh_json)


@router.get("/id/{facility_id}/notices", response_model=NoticeOut | None)
async def get_latest_notices(facility_id: int, db: Session = Depends(get_session)):
    latest = fetch_latest_notice_for_one(db, facility_id)
    return map_notice(latest)  # returns None → FastAPI responds with `null`


@router.get("/id/{facility_id}/meals", response_model=MealOut)
async def get_latest_meals(facility_id: int, db: Session = Depends(get_session)):
    latest = fetch_latest_meal_for_one(db, facility_id)
    if not latest:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="No meals found")
    return map_meal(latest)


@router.get("/uuid/{facility_uuid}/image")
async def get_facility_image_by_uuid(
        facility_uuid: UUID,
        db: Session = Depends(get_session),
):
    return serve_image_by_uuid(db, facility_uuid)


# @router.get("/id/{facility_id}/image")
# async def get_facility_image_by_id(
#         facility_id: int,
#         db: Session = Depends(get_session),
# ):
#     return serve_image_by_id(db, facility_id)

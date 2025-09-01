from http import HTTPStatus
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.src.config.database import Facility


def fetch_facilities(db: Session,
                     organization_id: int,
                     location_id: Optional[int] = None,
                     type_id: Optional[int] = None,
                     ) -> list[Facility]:
    stmt = (
        select(Facility)
        .where(Facility.organization_id == organization_id)
        .options(
            selectinload(Facility.location),
            selectinload(Facility.facility_type),
        )
    )
    if location_id is not None:
        stmt = stmt.where(Facility.location_id == location_id)
    if type_id is not None:
        stmt = stmt.where(Facility.facility_type_id == type_id)

    return db.exec(stmt).all()


def fetch_facility_by_uuid(uuid: UUID, db: Session) -> Facility:
    stmt = (
        select(Facility)
        .where(Facility.uuid == str(uuid))
        .options(
            selectinload(Facility.location),
            selectinload(Facility.facility_type),
        )
    )

    facility = db.exec(stmt).first()

    if facility is None:
        raise HTTPException(HTTPStatus.NOT_FOUND, detail="Facility not found")

    return facility


def fetch_facility_by_id(facility_id: int, db: Session) -> Facility:
    stmt = (
        select(Facility)
        .where(Facility.id == facility_id)
        .options(
            selectinload(Facility.location),
            selectinload(Facility.facility_type),
        )
    )

    facility = db.exec(stmt).first()

    if facility is None:
        raise HTTPException(HTTPStatus.NOT_FOUND, detail="Facility not found")

    return facility
from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.src.config.database import get_session, Location

router = APIRouter(prefix="/locations",
                   tags=["Location"])


@router.get("/",
            response_model=List[Location])
async def get_all_locations(db: Session = Depends(get_session)):
    locations: List[Location] = db.exec(select(Location)).all()
    return locations

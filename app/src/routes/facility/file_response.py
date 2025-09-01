from http import HTTPStatus
from pathlib import Path
from typing import Tuple, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session
from starlette.responses import FileResponse

from app.src.config.database import Facility
from app.src.routes.facility.queries import fetch_facility_by_uuid, fetch_facility_by_id

IMAGES_DIR = Path(__file__).resolve().parents[4] / "assets" / "images"
IMAGE_CANDIDATES: Tuple[Tuple[str, str], ...] = (
    ("jpg",  "image/jpeg"),
    ("jpeg", "image/jpeg"),
    ("png",  "image/png"),
    ("webp", "image/webp"),
)

def _find_image_for_uuid(uuid_str: str) -> Optional[Tuple[Path, str]]:
    """Return (absolute_path, mime) or None for a given UUID string."""
    for ext, mime in IMAGE_CANDIDATES:
        p = IMAGES_DIR / f"{uuid_str}.{ext}"
        if p.exists():
            return p, mime
    return None

def _file_response(path: Path, mime: str) -> FileResponse:
    return FileResponse(
        path=str(path),
        media_type=mime,
        filename=path.name,
        headers={"Cache-Control": "public, max-age=86400"},  # 1 day
    )

def serve_image_by_uuid(db: Session, facility_uuid: UUID) -> FileResponse:
    # Ensure facility exists (prevents scanning for arbitrary files)
    _ = fetch_facility_by_uuid(uuid=str(facility_uuid), db=db)

    resolved = _find_image_for_uuid(str(facility_uuid))
    if not resolved:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Image not found")
    path, mime = resolved
    return _file_response(path, mime)

def serve_image_by_id(db: Session, facility_id: int) -> FileResponse:
    # Fetch facility to get its UUID
    facility: Facility = fetch_facility_by_id(facility_id=facility_id, db=db)
    resolved = _find_image_for_uuid(facility.uuid)
    if not resolved:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Image not found")
    path, mime = resolved
    return _file_response(path, mime)
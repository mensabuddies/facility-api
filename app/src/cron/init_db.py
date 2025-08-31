"""
This script seeds the database. It reads the provided facilites.json file and inserts the seed data to the database.
"""

from __future__ import annotations

import json
from pathlib import Path

# --- make the import robust no matter where you run this file ---
import sys
ROOT = Path(__file__).resolve()
# adjust as needed; this tries to find the project root containing the "app" folder
for _ in range(5):
    if (ROOT.parent / "app").exists():
        sys.path.append(str(ROOT.parent))
        break
    ROOT = ROOT.parent

from sqlmodel import Session, select

# Your final models/engine live here:
from app.src.config.database import (
    engine, create_db_and_tables,
    Organization, Location, FacilityType, Facility,
)

BASE_DIR = (Path(__file__).resolve().parent.parent.parent.parent)  # where this script lives
FACILITIES_FILE = (BASE_DIR / "assets" / "facilities.json").resolve()

def get_or_create(session: Session, model, where: dict, defaults: dict | None = None):
    """Simple upsert-ish helper: fetch by unique fields; create if missing."""
    stmt = select(model)
    for k, v in where.items():
        stmt = stmt.where(getattr(model, k) == v)
    obj = session.exec(stmt).first()
    if obj:
        return obj, False
    payload = {**where, **(defaults or {})}
    obj = model(**payload)
    session.add(obj)
    session.flush()  # assign PKs
    return obj, True

def truncate(s: str | None, max_len: int) -> str | None:
    if s is None:
        return None
    return s if len(s) <= max_len else s[:max_len]

def main():
    # Ensure tables exist
    create_db_and_tables()

    with open(FACILITIES_FILE, encoding="utf-8") as f:
        data = json.load(f)  # top-level list of organizations

    with Session(engine) as session:
        # Prepare facility types
        ft_canteen, _ = get_or_create(session, FacilityType, {"name": "Canteen"})
        ft_cafeteria, _ = get_or_create(session, FacilityType, {"name": "Cafeteria"})

        for org_item in data:
            org, _ = get_or_create(
                session,
                Organization,
                {"name": org_item["organization_name"]},
                {"domain": org_item["organization_domain"]},
            )

            for loc_item in org_item.get("facilities", []):
                loc, _ = get_or_create(session, Location, {"name": loc_item["location"]})

                # Helper to insert facilities from a collection with a given type
                def seed_facilities(items, ftype: FacilityType):
                    for it in items:
                        # Map JSON → DB fields
                        uuid = it["id"]  # JSON id == DB uuid
                        name = truncate(it["facility_name"], 100)
                        address = truncate(it.get("address", ""), 100)
                        description = truncate(it.get("description", ""), 250)

                        # Skip if this UUID already exists
                        existing = session.exec(select(Facility).where(Facility.uuid == uuid)).first()
                        if existing:
                            continue

                        fac = Facility(
                            uuid=uuid,
                            name=name,
                            address=address,
                            description=description,
                            organization=org,
                            location=loc,
                            facility_type=ftype,
                        )
                        session.add(fac)

                seed_facilities(loc_item.get("canteens", []), ft_canteen)
                seed_facilities(loc_item.get("cafeterias", []), ft_cafeteria)

        session.commit()
        print("✅ Seeding complete.")

if __name__ == "__main__":
    main()

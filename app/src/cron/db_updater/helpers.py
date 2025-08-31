from sqlmodel import Session, select

from app.src.config.database import Facility as DBFacility
from app.src.cron.db_updater.detail_parser import parse_html_detail
from app.src.cron.db_updater.meal_parser import parse_html_menu
from app.src.cron.db_updater.schema import Facility as FacilitySchema


class DynamicFacility:
    """
    Gets you dynamic information, i.e. meals, opening hours and notices.
    """
    # For future extensions: inspect the returned parsed objects.
    # There is way more information parsed than we store in the database currently.

    db_facility: DBFacility = None
    db: Session = None
    detail = None
    menu = None

    def __init__(self, facility: FacilitySchema, db: Session):
        self.db_facility: DBFacility = db.exec(select(DBFacility).where(DBFacility.uuid == facility.id)).first()
        if not self.db_facility:
            raise ValueError(f"No facility found with uuid={facility.id}")
        self.detail = parse_html_detail(facility.detail_html)

        if self.db_facility.facility_type.name == "Canteen":
            self.menu = parse_html_menu(facility.menu_html)

    def get_facility(self) -> DBFacility:
        return self.db_facility

    def get_notices(self):
        return self.detail['notices_html']

    def get_menu(self):
        if not self.menu:
            raise TypeError("Cafeteria has no menu.")

        return self.menu['weeks']

    def is_canteen(self):
        return self.db_facility.facility_type.name == "Canteen"

    def get_opening_hours(self):
        return self.detail['opening_times']['by_day']
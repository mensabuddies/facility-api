"""
This cronjob takes the fetched results from fetcher.py, parses them and stores them in the database.
"""
from typing import List

from sqlmodel import select

from app.src.cron.db_updater.helpers import DynamicFacility
from app.src.cron.db_updater.schema import OrganizationBlock, LocationFacilities, Facility as FacilitySchema
from content_loader import ContentLoader
from app.src.config.database import get_session, Facility, Notice, OpeningHour, Meal


def main():
    content_loader = ContentLoader()
    swerk_wue: OrganizationBlock = content_loader.load_content().organizations[0]

    locations: list[LocationFacilities] = swerk_wue.facilities

    generator = get_session()  # create the generator
    db = next(generator)  # get the Session it yields
    try:
        for location in locations:
            all_facilities: list[FacilitySchema] = location.canteens + location.cafeterias

            for facility in all_facilities:
                dyn_facility: DynamicFacility = DynamicFacility(facility, db)
                # Store Notices
                new_notice: Notice = Notice(
                    facility = dyn_facility.get_facility(),
                    notices = dyn_facility.get_notices(),
                )
                db.add(new_notice)

                # Store Opening Hours
                new_opening_hours: OpeningHour = OpeningHour(
                    facility = dyn_facility.get_facility(),
                    opening_hours = dyn_facility.get_opening_hours()
                )
                db.add(new_opening_hours)

                if dyn_facility.is_canteen():
                    # Store Meals
                    new_meals: Meal = Meal(
                        facility=dyn_facility.get_facility(),
                        meals=dyn_facility.get_menu()
                    )
                    db.add(new_meals)

                db.commit()


    finally:
        generator.close()  # important: close so the contextmanager runs

if __name__ == "__main__":
    main()

from pydantic import BaseModel


class OpeningHoursPerDay(BaseModel):
    opens: str | None = None
    closes: str | None = None
    food_until: str | None = None


class OpeningHoursOutput(BaseModel):
    monday: OpeningHoursPerDay | None = None
    tuesday: OpeningHoursPerDay | None = None
    wednesday: OpeningHoursPerDay | None = None
    thursday: OpeningHoursPerDay | None = None
    friday: OpeningHoursPerDay | None = None
    saturday: OpeningHoursPerDay | None = None
    sunday: OpeningHoursPerDay | None = None
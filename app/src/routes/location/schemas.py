from pydantic import BaseModel


class LocationOut(BaseModel):
    id: int
    name: str

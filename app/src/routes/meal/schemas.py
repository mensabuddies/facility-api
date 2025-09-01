from typing import Any
from pydantic import BaseModel

class MealOut(BaseModel):
    meals: Any

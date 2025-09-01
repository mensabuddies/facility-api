from typing import Optional
from app.src.config.database import Meal
from app.src.routes.meal.schemas import MealOut

def map_meal(m: Optional[Meal]) -> Optional[MealOut]:
    if not m:
        return None
    return MealOut(meals=m.meals)

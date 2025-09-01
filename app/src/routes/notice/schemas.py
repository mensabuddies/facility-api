from pydantic import BaseModel
from typing import Any


class NoticeOut(BaseModel):
    notices: Any

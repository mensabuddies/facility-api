from typing import Optional
from app.src.config.database import Notice
from app.src.routes.notice.schemas import NoticeOut

def map_notice(n: Optional[Notice]) -> Optional[NoticeOut]:
    if not n:
        return None
    return NoticeOut(notices=n.notices)

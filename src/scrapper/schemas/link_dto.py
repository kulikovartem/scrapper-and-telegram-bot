from pydantic import BaseModel
from typing import List


class LinkDTO(BaseModel):
    link_id: int
    tg_id: int
    link: str
    date: str
    filters: List[str]
    tags: List[str]

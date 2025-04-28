from pydantic import BaseModel, HttpUrl
from typing import List


class LinkUpdate(BaseModel):
    id: int
    url: HttpUrl
    description: str
    tgChatIds: List[int]

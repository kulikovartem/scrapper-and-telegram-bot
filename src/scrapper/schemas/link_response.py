from pydantic import BaseModel, HttpUrl
from typing import List


class LinkResponse(BaseModel):
    id: int
    url: HttpUrl
    tags: List[str]
    filters: List[str]

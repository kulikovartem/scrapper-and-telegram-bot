from pydantic import BaseModel, HttpUrl
from typing import List


class AddLinkRequest(BaseModel):
    link: HttpUrl
    tags: List[str]
    filters: List[str]

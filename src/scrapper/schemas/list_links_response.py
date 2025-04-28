from pydantic import BaseModel
from typing import List
from src.scrapper.schemas.link_response import LinkResponse


class ListLinksResponse(BaseModel):
    links: List[LinkResponse]
    size: int

from pydantic import BaseModel, HttpUrl


class RemoveTagRequest(BaseModel):
    url: HttpUrl
    tag: str

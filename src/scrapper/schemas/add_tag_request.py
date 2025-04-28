from pydantic import BaseModel, HttpUrl


class AddTagRequest(BaseModel):
    url: HttpUrl
    tag: str

from pydantic import BaseModel, HttpUrl


class RemoveLinkRequest(BaseModel):
    link: HttpUrl

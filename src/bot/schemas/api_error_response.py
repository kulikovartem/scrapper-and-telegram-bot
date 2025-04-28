from pydantic import BaseModel
from typing import List


class ApiErrorResponse(BaseModel):
    description: str
    code: str
    exceptionName: str
    exceptionMessage: str
    stacktrace: List[str]

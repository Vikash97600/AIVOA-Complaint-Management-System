from pydantic import BaseModel, ConfigDict
from typing import Generic, TypeVar, List

T = TypeVar("T")

class APIMessage(BaseModel):
    message: str

class ErrorResponse(BaseModel):
    detail: str

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int

    model_config = ConfigDict(from_attributes=True)

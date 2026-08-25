from typing import Generic, TypeVar

from pydantic import BaseModel


T = TypeVar("T")

class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total_pages: int
    total_result: int
    q_text: str | None = None

class APIResponse(BaseModel, Generic[T]):
    status_code: int
    message: str
    data: T


# class PaginationData(BaseModel, Generic[T]):
#     data: list[T]
#     meta: PaginationMeta

class PaginatedResponse(BaseModel, Generic[T]):
    status_code: int
    message: str
    data: list[T]
    meta: PaginationMeta
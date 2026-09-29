from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Optional, Any
from datetime import datetime
from .base_schema import PaginatedResponse, PaginationMeta

class DocumentResponse(BaseModel):
    id: int
    title: str
    content: str
    filename: str
    original_file_path: Optional[str] = None
    extension: Optional[str] = None
    file_size: Optional[int] = 0
    metadata: Optional[Dict[str, Any]] = Field(default=None, alias="doc_metadata")
    embedded: bool = False
    generating_embedding: bool = False
    deleting_embedding: bool = False
    total_chunks: int = 0
    embedd_generation_started: Optional[datetime] = None
    embedd_generation_ended: Optional[datetime] = None
    embedd_deletion_started: Optional[datetime] = None
    embedd_deletion_ended: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class DocumentCreate(BaseModel):
    title: str
    content: str
    filename: str
    original_file_path: Optional[str] = None
    extension: Optional[str] = None
    file_size: Optional[int] = 0
    metadata: Optional[Dict[str, Any]] = None
    embedded: bool = False
    generating_embedding: bool = False
    deleting_embedding: bool = False
    total_chunks: int = 0
    embedd_generation_started: Optional[datetime] = None
    embedd_generation_ended: Optional[datetime] = None
    embedd_deletion_started: Optional[datetime] = None
    embedd_deletion_ended: Optional[datetime] = None

class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    generate_embedding: Optional[bool] = False


# class DocumentListResponse( BaseModel ):
#       data: list[DocumentResponse]
#       page: int
#       page_size: int
#       q_text: str | None = None
#       total_pages: int
#       total_result: int
class DocumentAnalytics(BaseModel):
    total_chunks: int = 0
    total_storage_used: int = 0


class DocumentListResponse(BaseModel):
    status_code: int = 200
    message: str = "Documents fetched successfully."
    data: list[DocumentResponse]
    meta: PaginationMeta
    analytics: DocumentAnalytics
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Optional, Any
from datetime import datetime
from .base_schema import PaginatedResponse

class DocumentResponse(BaseModel):
    id: int
    title: str
    content: str
    filename: str
    extension: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default=None, alias="doc_metadata")
    embedded: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class DocumentCreate(BaseModel):
    title: str
    content: str
    filename: str
    extension: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    embedded: int = 0

class DocumentUpdate( BaseModel ):
    metadata: Optional[Dict[str, Any]] = None
    embedded: int = 0

# class DocumentListResponse( BaseModel ):
#       data: list[DocumentResponse]
#       page: int
#       page_size: int
#       q_text: str | None = None
#       total_pages: int
#       total_result: int
DocumentListResponse = PaginatedResponse[  DocumentResponse  ]
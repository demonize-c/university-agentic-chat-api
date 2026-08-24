from pydantic import BaseModel
from typing import Dict, Optional, Any
from datetime import datetime


class DocumentResponse(BaseModel):
    id: int
    title: str
    content: str
    filename: str
    metadata: Optional[Dict[str, Any]] = None
    embedded: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DocumentCreate(BaseModel):
    title: str
    content: str
    filename: str
    metadata: Optional[Dict[str, Any]] = None
    embedded: int
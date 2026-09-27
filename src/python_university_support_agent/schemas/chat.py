from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ChatMessageRequest(BaseModel):
    query: str = Field(..., description="User message or question")
    doc_id: Optional[int] = Field(default=None, description="Optional document ID to scope similarity search")
    k: int = Field(default=4, ge=1, le=10, description="Top-k chunk results to retrieve")
    model_id: Optional[str] = Field(default=None, description="Optional model selection e.g. gemini-1.5-flash, google/gemma-2-9b-it")



class ChatSourceItem(BaseModel):
    content: str
    source: str
    page: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatMessageResponse(BaseModel):
    query: str
    reply: str
    sources: List[ChatSourceItem]

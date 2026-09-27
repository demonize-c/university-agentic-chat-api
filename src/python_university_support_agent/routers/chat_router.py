from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..schemas import APIResponse, ChatMessageRequest, ChatMessageResponse, ChatSourceItem
from ..retrieval import get_vector_store, get_embeddings
from ..crud import get_document_by_id
from ..logger import get_logger

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = get_logger("Chat API")

embeddings = get_embeddings()
vector_store = get_vector_store(embeddings)


@router.post("/message", response_model=APIResponse[ChatMessageResponse])
@router.post("/reply", response_model=APIResponse[ChatMessageResponse])
async def send_message(
    req: ChatMessageRequest,
    db: AsyncSession = Depends(get_db)
):
    target_filename = None
    if req.doc_id is not None:
        doc = await get_document_by_id(db, req.doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail=f"Document with ID {req.doc_id} not found")
        target_filename = doc.filename

    # Perform vector similarity search
    results = vector_store.similarity_search(query=req.query, k=req.k)

    # Filter by target document if doc_id was specified
    if target_filename:
        results = [
            doc for doc in results
            if doc.metadata.get("source") == target_filename or doc.metadata.get("source") == Path(target_filename).name
        ]

    sources: list[ChatSourceItem] = []
    context_snippets = []

    for doc in results:
        page_num = doc.metadata.get("page")
        source_name = doc.metadata.get("source", "Document")
        sources.append(ChatSourceItem(
            content=doc.page_content,
            source=str(source_name),
            page=int(page_num) if page_num is not None else None,
            metadata=doc.metadata
        ))
        context_snippets.append(doc.page_content.strip())

    if context_snippets:
        combined_context = "\n\n".join(context_snippets[:3])
        reply = f"Based on the retrieved context:\n\n{combined_context}"
    else:
        reply = "No relevant context found in the document embeddings for your query."

    response_data = ChatMessageResponse(
        query=req.query,
        reply=reply,
        sources=sources
    )

    return APIResponse(
        status_code=200,
        message="Reply generated successfully",
        data=response_data
    )

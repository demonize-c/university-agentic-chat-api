from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..schemas import APIResponse, ChatMessageRequest, ChatMessageResponse
from ..services import process_chat_request
from ..logger import get_logger

from ..config import settings

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = get_logger("Chat API")


@router.post("/message", response_model=APIResponse[ChatMessageResponse])
@router.post("/reply", response_model=APIResponse[ChatMessageResponse])
async def send_message(
    req: ChatMessageRequest,
    db: AsyncSession = Depends(get_db)
):
    active_model = req.model_id or settings.chat_model_id
    search_scope = f"Document #{req.doc_id}" if req.doc_id is not None else "All Documents"

    logger.info(
        "Processing Chat Request | query='%s' | Search Scope=%s | Active Model='%s'",
        req.query,
        search_scope,
        active_model
    )
    try:
        response_data = await process_chat_request(
            query=req.query,
            doc_id=req.doc_id,
            k=req.k,
            db=db,
            model_id=req.model_id
        )

        logger.info("Chat Request Completed Successfully for query='%s'", req.query)
        return APIResponse(
            status_code=200,
            message="Reply generated successfully",
            data=response_data
        )


    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing chat query: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing your request")


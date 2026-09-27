from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..schemas import APIResponse, ChatMessageRequest, ChatMessageResponse
from ..services import process_chat_request
from ..logger import get_logger

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = get_logger("Chat API")


@router.post("/message", response_model=APIResponse[ChatMessageResponse])
@router.post("/reply", response_model=APIResponse[ChatMessageResponse])
async def send_message(
    req: ChatMessageRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        response_data = await process_chat_request(
            query=req.query,
            doc_id=req.doc_id,
            k=req.k,
            db=db
        )

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


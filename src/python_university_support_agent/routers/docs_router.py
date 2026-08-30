from fastapi import APIRouter, Depends, Query, Request
from ..schemas import DocumentCreate, DocumentResponse, APIResponse
from fastapi import Form, File, UploadFile, HTTPException
from typing import Annotated
import json
from ..utils import extract_file, save_file
from ..crud import get_documents, create_document
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..logger import get_logger
from python_university_support_agent.services import create_job

router = APIRouter(prefix="/docs", tags=["Docs"])


ALLOWED_EXTENSION = [".pdf",".docx",".txt"]

logger = get_logger("Docs API")

@router.get("/")
async def get_docs(
    page: int = Query(1, gt= 0),
    page_size: int = Query(10, gt=0, le= 25),
    q_text: str = None,
    db: AsyncSession = Depends(get_db)
):
    return await get_documents( db= db,page= page, page_size= page_size, q_text= q_text)

        

@router.post("/upload", response_model = APIResponse[DocumentResponse])
async def upload_docs(
   metadata: Annotated[str,Form(...)],
   file: Annotated[UploadFile, File(...)],
   request: Request,
   db: AsyncSession = Depends(get_db)
):
    filename = file.filename or "file"
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in [".pdf",".docx",".txt"]:
        raise HTTPException(400, detail= "File type is not allowed")
    
    file_raw_content = await file.read()
    file_size_mb =  ( len(file_raw_content)/ (1024 * 1024) )
    await file.seek(0)

    if file_size_mb > 50:
         raise HTTPException(400, detail= "File size is not allowed more than 50 mb.")

    parsed_metadata = {}
    if metadata:
        try:
            parsed_metadata = json.loads( metadata)
        except(json.JSONDecodeError, ValueError):
            raise HTTPException(400, detail = "metadata must be valid JSON object.")

    file_text_content = "<No content>"

    try:
        upload_filename = await save_file(file, "documents")
        # Create document without committing yet (commit=False)
        doc = await create_document(db, DocumentCreate(
            title     = filename,
            content   = file_text_content,
            filename  = upload_filename,
            metadata  = parsed_metadata,
            extension = ext,
            embedded  = 0
        ), commit=False)
       
        # Create job and commit the entire transaction atomically (commit=True)
        job = await create_job(db, document_id= doc.id, commit=True)

        redis  = request.app.state.redis
        if redis:
            job = await redis.enqueue_job(
                        "create_embedd",
                         job.id,
                        _queue_name = "embedd_docs_queue"
                    )
            logger.info("create doc embedd job is scheduled.")
        return APIResponse(data=doc, status_code= 201, message="Success")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
    
    


    
    
    



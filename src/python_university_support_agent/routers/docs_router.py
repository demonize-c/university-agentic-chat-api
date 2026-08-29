from fastapi import APIRouter, Depends, Query, Request
from ..schemas import DocumentCreate, DocumentResponse
from fastapi import Form, File, UploadFile, HTTPException
from typing import Annotated
import json
from ..utils import extract_file, save_file
from ..crud import get_documents, create_document
from sqlalchemy.orm import Session
from ..db import get_db
from ..logger import get_logger
router = APIRouter(prefix="/docs", tags=["Docs"])


ALLOWED_EXTENSION = [".pdf",".docx",".txt"]

loggger = get_logger("Docs API")

@router.get("/")
async def  get_docs(
    page: int = Query(1, gt= 0),
    page_size: int = Query(10, gt=0, le= 25),
    q_text: str = None,
    db = Depends(get_db)
):
    return await get_documents( db= db,page= page, page_size= page_size, q_text= q_text)



@router.post("/upload", response_model = str)
async def upload_docs(
   metadata: Annotated[str,Form(...)],
   file: Annotated[UploadFile, File(...)],
   request: Request,
   db: Session = Depends(get_db),
) -> str :

    upload_file_path = save_file( file = file, dir = "documents")

    return upload_file_path
# @router.post("/upload", response_model = str)
# async def upload_docs(
#    metadata: Annotated[str,Form(...)],
#    file: Annotated[UploadFile, File(...)],
#    request: Request,
#    db: Session = Depends(get_db),
# ) -> str :
#     redis  = request.app.state.redis
#     if redis:
#         job = await redis.enqueue_job(
#                     "create_embedd",
#                      123,
#                      _queue_name = "embedd_docs_queue"
#                 )
#         loggger.info("create doc embedd job is scheduled.")
        
#     else:
#         loggger.info("Job not scheduled. Redis not configured.")

#     return "ok"


        

# @router.post("/upload", response_model = DocumentResponse)
# async def upload_docs(
#    metadata: Annotated[str,Form(...)],
#    file: Annotated[UploadFile, File(...)],
#    db: Session = Depends(get_db)
# ):
#     filename = file.filename or "file"
#     ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

#     if ext not in [".pdf",".docx",".txt"]:
#         raise HTTPException(400, detail= "File type is not allowed")
    
#     file_raw_content = await file.read()
#     file_size_mb =  ( len(file_raw_content)/ (1024 * 1024) )
#     await file.seek(0)

#     if file_size_mb > 2:
#          raise HTTPException(400, detail= "File size is not allowed more than 2 mb.")

#     parsed_metadata = {}
#     if metadata:
#         try:
#             parsed_metadata = json.loads( metadata)
#         except(json.JSONDecodeError, ValueError):
#             raise HTTPException(400, detail = "metadata must be valid JSON object.")

#     try:
#        file_text_content = await extract_file( file )
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))

#     try:
#         doc = create_document(db, DocumentCreate(
#             title     = filename,
#             content   = file_text_content,
#             filename  = filename,
#             metadata  = parsed_metadata,
#             extension = ext,
#             embedded  = 0
#         ))
#         return doc
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
    
    


    
    
    



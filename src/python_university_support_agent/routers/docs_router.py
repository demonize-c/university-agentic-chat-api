from pathlib import Path
from fastapi import APIRouter, Depends, Query, Request, Form, File, UploadFile, HTTPException
from typing import Annotated
import json
from ..schemas import DocumentCreate, DocumentUpdate, DocumentResponse, APIResponse
from ..crud import get_documents, create_document, get_document_by_id, update_document, delete_document
from ..utils import extract_file, save_file
from ..config import settings
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
        saved_info = await save_file(file, "documents")
        parsed_metadata["original_file_path"] = saved_info["original_file_path"]
        parsed_metadata["original_extension"] = saved_info["original_ext"]

        # Create document with title as original filename, and filename as PDF path
        doc = await create_document(db, DocumentCreate(
            title     = saved_info["original_title"],
            content   = file_text_content,
            filename  = saved_info["pdf_file_path"],
            metadata  = parsed_metadata,
            extension = ".pdf",
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
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@router.get("/{doc_id}", response_model=APIResponse[DocumentResponse])
async def get_doc(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc = await get_document_by_id(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document with ID {doc_id} not found")
    return APIResponse(status_code=200, message="Document fetched successfully", data=DocumentResponse.model_validate(doc))


@router.patch("/{doc_id}", response_model=APIResponse[DocumentResponse])
@router.put("/{doc_id}", response_model=APIResponse[DocumentResponse])
async def update_doc(doc_id: int, doc_in: DocumentUpdate, db: AsyncSession = Depends(get_db)):
    doc = await update_document(db, doc_id=doc_id, doc_in=doc_in)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document with ID {doc_id} not found")
    return APIResponse(status_code=200, message="Document updated successfully", data=DocumentResponse.model_validate(doc))


@router.delete("/{doc_id}", response_model=APIResponse[dict])
async def delete_doc(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc = await get_document_by_id(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document with ID {doc_id} not found")

    # Remove vector embeddings from ChromaDB
    try:
        from ..retrieval import get_vector_store, get_embeddings
        vector_store = get_vector_store(get_embeddings())
        vector_store._collection.delete(where={"source": doc.filename})
        logger.info(f"Vector embeddings for document {doc.filename} deleted from vector store")
    except Exception as e:
        logger.warning(f"Error removing vector embeddings for doc {doc_id}: {e}")

    # Remove stored physical files if present
    try:
        pdf_abs_path = settings.storage_dir.joinpath(doc.filename)
        if pdf_abs_path.exists():
            pdf_abs_path.unlink()

        if doc.doc_metadata and "original_file_path" in doc.doc_metadata:
            orig_abs_path = settings.storage_dir.joinpath(doc.doc_metadata["original_file_path"])
            if orig_abs_path.exists() and orig_abs_path != pdf_abs_path:
                orig_abs_path.unlink()
    except Exception as e:
        logger.warning(f"Error removing physical files for doc {doc_id}: {e}")

    deleted = await delete_document(db, doc_id)
    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to delete document record")

    return APIResponse(status_code=200, message="Document deleted successfully", data={"id": doc_id})



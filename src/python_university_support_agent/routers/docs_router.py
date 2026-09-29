from pathlib import Path
from fastapi import APIRouter, Depends, Query, Request, Form, File, UploadFile, HTTPException
from typing import Annotated, Optional
from datetime import datetime, timezone
import json
from ..schemas import DocumentCreate, DocumentUpdate, DocumentResponse, DocumentListResponse, APIResponse
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

@router.get("/", response_model=DocumentListResponse)
async def get_docs(
    page: int = Query(1, gt= 0),
    page_size: int = Query(10, gt=0, le= 25),
    q_text: str = None,
    db: AsyncSession = Depends(get_db)
):
    return await get_documents( db= db,page= page, page_size= page_size, q_text= q_text)

        

@router.post("/upload", response_model = APIResponse[DocumentResponse])
async def upload_docs(
   file: Annotated[UploadFile, File(...)],
   db: AsyncSession = Depends(get_db)
):
    filename = file.filename or "file"
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in [".pdf",".docx",".txt"]:
        raise HTTPException(400, detail= "File type is not allowed")
    
    file_raw_content = await file.read()
    file_size_bytes = len(file_raw_content)
    file_size_mb = (file_size_bytes / (1024 * 1024))
    await file.seek(0)

    if file_size_mb > 50:
         raise HTTPException(400, detail= "File size is not allowed more than 50 mb.")

    file_text_content = "<No content>"

    try:
        saved_info = await save_file(file, "documents")

        # Create document with title as original filename, filename as PDF path, and dedicated columns for original_file_path, extension, and file_size
        doc = await create_document(db, DocumentCreate(
            title              = saved_info["original_title"],
            content            = file_text_content,
            filename           = saved_info["pdf_file_path"],
            original_file_path = saved_info["original_file_path"],
            extension          = saved_info["original_ext"],
            file_size          = file_size_bytes,
            metadata           = None,
            embedded           = False,
            generating_embedding = False,
            deleting_embedding = False,
            total_chunks       = 0
        ), commit=True)
       
        logger.info(f"Document ID<{doc.id}> uploaded successfully.")
        return APIResponse(data=doc, status_code=201, message="Document uploaded successfully")
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@router.post("/{doc_id}/embeddings/generate", response_model=APIResponse[DocumentResponse])
@router.post("/documents/{doc_id}/embeddings/generate", include_in_schema=False, response_model=APIResponse[DocumentResponse])
async def generate_doc_embeddings(
    doc_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    doc = await get_document_by_id(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document with ID {doc_id} not found")

    if doc.generating_embedding:
        raise HTTPException(status_code=400, detail="Embedding generation is already in progress for this document")

    if doc.deleting_embedding:
        raise HTTPException(status_code=400, detail="Embedding deletion is currently in progress for this document")

    doc.embedd_generation_started = datetime.now(timezone.utc)
    doc.embedd_generation_ended = None
    await db.commit()
    await db.refresh(doc)

    try:
        job = await create_job(db, document_id=doc.id, commit=True)
        redis = request.app.state.redis
        if not redis:
            raise HTTPException(status_code=503, detail="Background job queue service is not available")

        await redis.enqueue_job(
            "create_embedd",
            job.id,
            _queue_name="embedd_docs_queue"
        )
        logger.info(f"Embedding generation job queued for document ID<{doc_id}>")
        return APIResponse(data=DocumentResponse.model_validate(doc), status_code=202, message="Embedding generation triggered successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger embedding generation for doc ID<{doc_id}>: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger embedding generation: {str(e)}")


@router.delete("/{doc_id}/embeddings", response_model=APIResponse[DocumentResponse])
@router.delete("/documents/{doc_id}/embeddings", include_in_schema=False, response_model=APIResponse[DocumentResponse])
async def delete_doc_embeddings(
    doc_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    doc = await get_document_by_id(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document with ID {doc_id} not found")

    if doc.deleting_embedding:
        raise HTTPException(status_code=400, detail="Embedding deletion is already in progress for this document")

    if doc.generating_embedding:
        raise HTTPException(status_code=400, detail="Embedding generation is currently in progress for this document")

    doc.embedd_deletion_started = datetime.now(timezone.utc)
    doc.embedd_deletion_ended = None
    await db.commit()
    await db.refresh(doc)

    try:
        redis = request.app.state.redis
        if not redis:
            raise HTTPException(status_code=503, detail="Background job queue service is not available")

        await redis.enqueue_job(
            "delete_embedd",
            doc.id,
            _queue_name="embedd_docs_queue"
        )
        logger.info(f"Embedding deletion job queued for document ID<{doc_id}>")
        return APIResponse(data=DocumentResponse.model_validate(doc), status_code=202, message="Embedding deletion triggered successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger embedding deletion for doc ID<{doc_id}>: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger embedding deletion: {str(e)}")


@router.get("/{doc_id}", response_model=APIResponse[DocumentResponse])
async def get_doc(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc = await get_document_by_id(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document with ID {doc_id} not found")
    return APIResponse(status_code=200, message="Document fetched successfully", data=DocumentResponse.model_validate(doc))


@router.patch("/{doc_id}", response_model=APIResponse[DocumentResponse])
@router.put("/{doc_id}", response_model=APIResponse[DocumentResponse])
async def update_doc(
    doc_id: int,
    doc_in: DocumentUpdate,
    request: Request,
    generate_embedding: Optional[bool] = Query(default=None, description="Trigger embedding generation after updating document"),
    db: AsyncSession = Depends(get_db)
):
    doc = await get_document_by_id(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document with ID {doc_id} not found")

    should_generate = (generate_embedding is True) or (doc_in.generate_embedding is True)

    if should_generate:
        if doc.generating_embedding:
            raise HTTPException(status_code=400, detail="Embedding generation is already in progress for this document")
        if doc.deleting_embedding:
            raise HTTPException(status_code=400, detail="Embedding deletion is currently in progress for this document")

    updated_doc = await update_document(db, doc_id=doc_id, doc_in=doc_in, commit=True)

    if should_generate:
        updated_doc.embedd_generation_started = datetime.now(timezone.utc)
        updated_doc.embedd_generation_ended = None
        await db.commit()
        await db.refresh(updated_doc)

        try:
            job = await create_job(db, document_id=updated_doc.id, commit=True)
            redis = request.app.state.redis
            if not redis:
                raise HTTPException(status_code=503, detail="Background job queue service is not available")

            await redis.enqueue_job(
                "create_embedd",
                job.id,
                _queue_name="embedd_docs_queue"
            )
            logger.info(f"Embedding generation job queued via update_doc for document ID<{doc_id}>")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to trigger embedding generation in update_doc for doc ID<{doc_id}>: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to trigger embedding generation: {str(e)}")

    return APIResponse(status_code=200, message="Document updated successfully", data=DocumentResponse.model_validate(updated_doc))


@router.delete("/{doc_id}", response_model=APIResponse[dict])
async def delete_doc(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc = await get_document_by_id(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document with ID {doc_id} not found")

    if doc.generating_embedding or doc.deleting_embedding:
        raise HTTPException(status_code=400, detail="Cannot delete document while an embedding operation is in progress")

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

        orig_path_str = doc.original_file_path or (doc.doc_metadata.get("original_file_path") if doc.doc_metadata else None)
        if orig_path_str:
            orig_abs_path = settings.storage_dir.joinpath(orig_path_str)
            if orig_abs_path.exists() and orig_abs_path != pdf_abs_path:
                orig_abs_path.unlink()
    except Exception as e:
        logger.warning(f"Error removing physical files for doc {doc_id}: {e}")

    deleted = await delete_document(db, doc_id)
    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to delete document record")

    return APIResponse(status_code=200, message="Document deleted successfully", data={"id": doc_id})



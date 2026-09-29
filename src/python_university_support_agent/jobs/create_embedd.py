
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..config import settings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import pypdf
from docx import Document as DocxDocument
from langchain_core.documents import Document
from ..retrieval import get_vector_store, get_embeddings
from pathlib import Path
from io import BytesIO
from ..db import sessionLocal
from ..models import Document as DocumentModel
from ..logger import get_logger
from tenacity import retry, retry_if_exception_type, wait_exponential, stop_after_attempt
import asyncio
from python_university_support_agent.services import get_job, start_job, complete_job, update_progress, fail_job


PAGE_BATCH_SIZE = 5   # Read pages in batches of 5
EMBED_BATCH_SIZE = 10 # Send chunks to vector store in batches of 10

logger = get_logger("Embedd Job")

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,      # max characters per chunk
    chunk_overlap=200,    # overlap between chunks (preserves context across boundaries)
    add_start_index=True  # track index of chunk in original document
)

embeddings = get_embeddings()

vector_store = get_vector_store( embeddings )


async def get_page_batch_documents(
    reader: pypdf.PdfReader,
    filename: str,
    start_page: int,
    end_page: int,
    previous_overlap_doc: Document | None = None
) -> list[Document]:
    batch_docs = []
    if previous_overlap_doc is not None:
        batch_docs.append(previous_overlap_doc)

    for i in range(start_page, end_page):
        page_text = reader.pages[i].extract_text() or ""
        if page_text.strip():
            batch_docs.append(Document(
                page_content=page_text,
                metadata={"source": filename, "page": i + 1}
            ))
    return batch_docs


@retry(
       retry=retry_if_exception_type((TimeoutError, asyncio.TimeoutError, ConnectionError)),
       stop=stop_after_attempt(3),
       wait=wait_exponential(
            multiplier=1,
            min=2,
            max=60,
      ),
      reraise=True,
)
async def process_batch(batch: list[Document]):
    await asyncio.wait_for(
        vector_store.aadd_documents(batch),
        timeout= 60 * 5
    )

async def create_embedd(ctx, job_id):
    from ..logger import get_logger

    logger = get_logger(f"Job<{job_id}> | Embedd Task")
    async with sessionLocal() as db:
        try:
            existing_job = await get_job(db, job_id)
            if not existing_job:
                logger.warning(f"Job {job_id} not found in database (it may have been deleted). Skipping task.")
                return

            if not existing_job.document:
                logger.warning(f"Parent document for Job {job_id} not found (it may have been deleted). Skipping task.")
                return

            job = await start_job(db=db, job_id=job_id)
            doc = job.document

            logger = get_logger(f"Doc<{doc.filename}> | Embedd Task")
            logger.info("Task started")

            filename = doc.filename
            file_abs_path = Path.joinpath(settings.storage_dir, filename)
            file_path = Path(file_abs_path)

            if not file_path.exists():
                error_msg = f"File not found on disk: {file_abs_path}"
                logger.error(error_msg)
                await fail_job(db=db, job_id=job_id, error=error_msg)
                return

            reader = pypdf.PdfReader(file_path)
            total_pages = len(reader.pages)
            logger.info(f"Total {total_pages} PDF pages to read")

            all_page_docs = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    all_page_docs.append(Document(
                        page_content=page_text,
                        metadata={"source": filename, "page": i + 1}
                    ))

            # Split document into chunks
            all_splits = text_splitter.split_documents(all_page_docs)
            total_chunks_count = len(all_splits)
            logger.info(f"Generated {total_chunks_count} total chunks from {total_pages} pages")

            # Update document total_chunks field
            doc.total_chunks = total_chunks_count
            await update_progress(db=db, job_id=job.id, embedded_chunks=0, total_chunks=total_chunks_count)
            await db.commit()

            total_embedded_chunks = 0
            for i in range(0, total_chunks_count, EMBED_BATCH_SIZE):
                embed_batch = all_splits[i: i + EMBED_BATCH_SIZE]
                await process_batch(batch=embed_batch)
                total_embedded_chunks += len(embed_batch)

                await update_progress(
                    db=db,
                    job_id=job.id,
                    embedded_chunks=total_embedded_chunks,
                    total_chunks=total_chunks_count
                )
                logger.info(f"Embedded {total_embedded_chunks}/{total_chunks_count} chunks")

            await complete_job(db=db, job_id=job.id)
            logger.info(f"File {filename} embedding processed successfully ({total_embedded_chunks} chunks embedded)")
        except Exception as e:
            logger.error(f"Embedding job failed: {e}")
            try:
                await fail_job(db=db, job_id=job_id, error=str(e))
            except Exception as fail_err:
                logger.warning(f"Could not update failed state for job {job_id}: {fail_err}")
            raise e





from datetime import datetime, timezone
from ..db import sessionLocal
from ..models import Document as DocumentModel
from ..logger import get_logger
from ..retrieval import get_vector_store, get_embeddings

logger = get_logger("Delete Embedd Job")


async def delete_embedd(ctx, document_id: int):
    logger.info(f"Starting embedding deletion job for Doc ID<{document_id}>")
    async with sessionLocal() as db:
        doc = await db.get(DocumentModel, document_id)
        if not doc:
            logger.error(f"Document ID<{document_id}> not found for deletion job")
            return

        # Mark document as deleting in background job
        doc.deleting_embedding = True
        doc.generating_embedding = False
        await db.commit()
        await db.refresh(doc)

        try:
            vector_store = get_vector_store(get_embeddings())
            vector_store._collection.delete(where={"source": doc.filename})
            logger.info(f"Vector embeddings for document {doc.filename} deleted successfully from vector store")

            doc.embedded = False
            doc.deleting_embedding = False
            doc.generating_embedding = False
            doc.total_chunks = 0
            doc.embedd_deletion_ended = datetime.now(timezone.utc)
            await db.commit()
            logger.info(f"Doc ID<{document_id}> embedding state updated: embedded=False, deleting_embedding=False, total_chunks=0")
        except Exception as e:
            logger.error(f"Embedding deletion job failed for Doc ID<{document_id}>: {e}")
            try:
                doc.deleting_embedding = False
                doc.embedd_deletion_ended = datetime.now(timezone.utc)
                await db.commit()
            except Exception as commit_err:
                logger.error(f"Failed to commit deletion failure state: {commit_err}")
            raise e


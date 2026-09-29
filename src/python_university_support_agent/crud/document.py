from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select, func, case
from ..schemas import PaginationMeta, DocumentResponse, DocumentListResponse, DocumentCreate, DocumentUpdate, APIResponse, DocumentAnalytics
from ..models  import Document
from math import ceil


async def create_document(db: AsyncSession, doc_in: DocumentCreate, commit: bool = True) -> Document:
    ext = doc_in.extension
    if not ext and "." in doc_in.filename:
        ext = doc_in.filename.rsplit(".", 1)[-1]

    doc = Document(
        title=doc_in.title,
        content=doc_in.content,
        filename=doc_in.filename,
        original_file_path=doc_in.original_file_path,
        extension=ext,
        file_size=doc_in.file_size,
        doc_metadata=doc_in.metadata,
        embedded=doc_in.embedded,
        generating_embedding=doc_in.generating_embedding,
        deleting_embedding=doc_in.deleting_embedding,
        total_chunks=doc_in.total_chunks,
        embedd_generation_started=doc_in.embedd_generation_started,
        embedd_generation_ended=doc_in.embedd_generation_ended,
        embedd_deletion_started=doc_in.embedd_deletion_started,
        embedd_deletion_ended=doc_in.embedd_deletion_ended,
    )

    db.add(doc)
    if commit:
        await db.commit()
        await db.refresh(doc)
    else:
        await db.flush()
    return doc


async def get_documents(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    q_text: str = None
) -> DocumentListResponse:
    stats_stmt = select(
        func.count(Document.id),
        func.coalesce(func.sum(case((Document.embedded == True, Document.total_chunks), else_=0)), 0),
        func.coalesce(func.sum(Document.file_size), 0)
    ).select_from(Document)
    if q_text:
        stats_stmt = stats_stmt.where(Document.title.icontains(q_text) | Document.content.icontains(q_text))

    stats_result = await db.execute(stats_stmt)
    total_result, total_chunks, total_storage_used = stats_result.one()
    total_result = total_result or 0
    total_chunks = int(total_chunks or 0)
    total_storage_used = int(total_storage_used or 0)

    # Fallback to vector store count if total_chunks in DB is 0
    if not q_text and total_chunks == 0:
        try:
            from ..retrieval import get_vector_store, get_embeddings
            vector_store = get_vector_store(get_embeddings())
            chroma_count = vector_store._collection.count()
            if chroma_count > 0:
                total_chunks = chroma_count
        except Exception:
            pass

    total_pages = ceil(total_result / page_size) if total_result > 0 else 0

    if total_pages > 0 and page > total_pages:
        page = total_pages
    skip = max(0, (page - 1) * page_size)

    query = select(Document).offset(skip).limit(page_size).order_by(Document.created_at)
    if q_text:
        query = select(Document).where(Document.title.icontains(q_text) | Document.content.icontains(q_text)).offset(skip).limit(page_size).order_by(Document.created_at)

    res = await db.execute(query)
    result = res.scalars().all()

    docs = [DocumentResponse(
        id=doc.id,
        title=doc.title,
        content=doc.content.strip()[:300],
        filename=doc.filename,
        original_file_path=doc.original_file_path,
        extension=doc.extension,
        file_size=doc.file_size,
        doc_metadata=doc.doc_metadata,
        embedded=bool(doc.embedded),
        generating_embedding=bool(doc.generating_embedding),
        deleting_embedding=bool(doc.deleting_embedding),
        total_chunks=doc.total_chunks or 0,
        embedd_generation_started=doc.embedd_generation_started,
        embedd_generation_ended=doc.embedd_generation_ended,
        embedd_deletion_started=doc.embedd_deletion_started,
        embedd_deletion_ended=doc.embedd_deletion_ended,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )
    for doc in result]

    return DocumentListResponse(
        status_code=200,
        message="Documents fetched successfully.",
        data=docs,
        meta=PaginationMeta(
            total_pages=total_pages,
            total_result=total_result,
            page=page,
            page_size=page_size,
            q_text=q_text
        ),
        analytics=DocumentAnalytics(
            total_chunks=total_chunks,
            total_storage_used=total_storage_used
        )
    )

async def get_document_by_id(db: AsyncSession, doc_id: int) -> Document | None:
    result = await db.execute(select(Document).where(Document.id == doc_id))
    return result.scalar_one_or_none()


async def update_document(
    db: AsyncSession,
    doc_id: int,
    doc_in: DocumentUpdate,
    commit: bool = True
) -> Document | None:
    doc = await get_document_by_id(db, doc_id)
    if not doc:
        return None

    if doc_in.title is not None:
        doc.title = doc_in.title

    if doc_in.metadata is not None:
        doc.doc_metadata = doc_in.metadata

    if commit:
        await db.commit()
        await db.refresh(doc)
    else:
        await db.flush()
    return doc


async def delete_document(db: AsyncSession, doc_id: int, commit: bool = True) -> bool:
    doc = await get_document_by_id(db, doc_id)
    if not doc:
        return False

    await db.delete(doc)
    if commit:
        await db.commit()
    else:
        await db.flush()
    return True


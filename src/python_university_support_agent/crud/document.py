from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select, func
from ..schemas import PaginationMeta, DocumentResponse, DocumentListResponse, DocumentCreate, APIResponse
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
        extension=ext,
        doc_metadata=doc_in.metadata,
        embedded=doc_in.embedded,
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
    count_stmt = select(func.count()).select_from(Document)
    if q_text:
        count_stmt = count_stmt.where(Document.title.icontains(q_text) | Document.content.icontains(q_text))

    count_result = await db.execute(count_stmt)
    total_result = count_result.scalar() or 0
    total_pages  = ceil(total_result / page_size) if total_result > 0 else 0

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
        extension=doc.extension,
        doc_metadata=doc.doc_metadata,
        embedded=doc.embedded,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )
    for doc in result]

    return DocumentListResponse(
        status_code= 200,
        message="Documents fetched successfully.",
        data = docs,
        meta = PaginationMeta(
            total_pages = total_pages,
            total_result = total_result,
            page = page,
            page_size = page_size
        )
    )


    
    
      
      


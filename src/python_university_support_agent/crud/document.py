from sqlalchemy.orm import Session
from sqlalchemy.sql import select, func
from ..schemas import PaginationMeta, DocumentResponse, DocumentListResponse, DocumentCreate
from ..models  import Document
from math import ceil


def create_document(db: Session, doc_in: DocumentCreate) -> DocumentResponse:
        ext = doc_in.extension
        if not ext and "." in doc_in.filename:
            ext = doc_in.filename.rsplit(".", 1)[-1]

        db_doc = Document(
            title=doc_in.title,
            content=doc_in.content,
            filename=doc_in.filename,
            extension=ext,
            doc_metadata=doc_in.metadata,
            embedded=doc_in.embedded,
        )

        db.add(db_doc)
        db.commit()
        db.refresh(db_doc)
        return db_doc


async def get_documents(
        db: Session,
        page: int = 1,
        page_size: int = 10,
        q_text: str = None
) -> DocumentListResponse:
      
    total_result = db.query(func.count(Document.id)).scalar() or 0
    total_pages  = ceil(total_result / page_size) if total_result > 0 else 0

    if total_pages > 0 and page > total_pages:
         page = total_pages
    skip = max(0, (page - 1) * page_size)

    query = select(
        Document
    ).offset( skip ).limit( page_size ).order_by(Document.created_at)

    result = db.execute( query ).scalars().all()

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


    
    
      
      


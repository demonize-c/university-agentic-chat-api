from sqlalchemy.orm import Session
from ..schemas import DocumentCreate, DocumentResponse
from ..models import Document


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


from sqlalchemy.orm import Session
from ..schemas import DocumentCreate
from ..models  import Document
 
def create_document(db: Session, doc: DocumentCreate):
   doc = Document(
      title    = DocumentCreate.title,
      content  = DocumentCreate.content,
      filename = DocumentCreate.filename,
      metadata = DocumentCreate.metadata,
      emebedded= DocumentCreate.embedded
   );

   db.add( doc )
   db.commit()
   db.flush()

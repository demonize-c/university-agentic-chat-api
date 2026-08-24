from sqlalchemy import Column, BigInteger, String, Text, DateTime, JSON
from ..db.session import Base
from datetime import datetime, timezone


class Document(Base):
    __tablename__ = "documents"

    id         = Column(BigInteger, primary_key=True, autoincrement=True)
    title      = Column( String, nullable=False)
    content    = Column( Text,   nullable= False)
    filename   = Column( String, nullable=False )
    extension  = Column( String, nullable=False)
    metadata   = Column(JSON)
    embedded   = Column(BigInteger, default=0)
    created_at = Column(DateTime, default= lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default= lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


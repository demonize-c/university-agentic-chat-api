from sqlalchemy import Column, BigInteger, String, Text, DateTime, JSON
from datetime import datetime, timezone
from ..db.session import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    filename = Column(String(255), nullable=False)
    extension = Column(String(50), nullable=True)
    doc_metadata = Column("metadata", JSON, nullable=True)
    embedded = Column(BigInteger, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


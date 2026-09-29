from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import String, Text, BigInteger, JSON, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.session import Base

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_file_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    extension: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, default=0)
    doc_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)
    embedded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    generating_embedding: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleting_embedding: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    total_chunks: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    embedd_generation_started: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    embedd_generation_ended: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    embedd_deletion_started: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    embedd_deletion_ended: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    jobs: Mapped[List["EmbeddingJob"]] = relationship(
        "EmbeddingJob",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin",
    )



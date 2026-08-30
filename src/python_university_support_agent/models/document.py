from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import String, Text, BigInteger, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.session import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    extension: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    doc_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)
    embedded: Mapped[int] = mapped_column(BigInteger, default=0)
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



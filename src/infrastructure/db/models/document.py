from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

from core.entities.document import DocumentType, DocumentCategory

Base = declarative_base()


class Document(Base):
    """Модель документа/файла"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)
    document_type = Column(
        Enum(DocumentType, name="document_type_enum"),
        nullable=False,
        default=DocumentType.OTHER,
    )
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)

    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)

    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    entity_id = Column(Integer, nullable=True)
    entity_type = Column(String(50), nullable=True)

    uploaded_at = Column(DateTime, nullable=False, default=datetime.now)

    is_primary = Column(Boolean, nullable=False, default=False)
    sort_order = Column(Integer, nullable=False, default=0)

    file_hash = Column(String(255), nullable=True)

    __table_args__ = (
        Index("idx_documents_asset_id", "asset_id"),
        Index("idx_documents_document_type", "document_type"),
        Index("idx_documents_uploaded_by", "uploaded_by"),
        Index("idx_documents_uploaded_at", "uploaded_at"),
        Index("idx_documents_file_hash", "file_hash"),
    )

    asset = relationship("Asset", back_populates="documents")
    uploaded_by_user = relationship(
        "User", back_populates="documents", foreign_keys=[uploaded_by]
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename='{self.filename}', type={self.document_type.value})>"

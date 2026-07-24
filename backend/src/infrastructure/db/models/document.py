# src/infrastructure/db/models/document.py
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    BigInteger,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Document(Base):
    """Модель документа/файла"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)  # Путь к файлу или URL
    file_size = Column(BigInteger, nullable=False)   # Размер в байтах
    mime_type = Column(String(100), nullable=False)  # image/jpeg, application/pdf и т.д.

    document_type = Column(String(50), nullable=False, default="other")
    category = Column(String(50), nullable=False, default="asset")

    entity_id = Column(Integer, nullable=True)       # ID связанной сущности
    entity_type = Column(String(50), nullable=True)  # 'asset', 'repair_request' и т.д.

    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)

    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, nullable=False, default=datetime.now)

    is_primary = Column(Boolean, nullable=False, default=False)
    sort_order = Column(Integer, nullable=False, default=0)

    file_hash = Column(String(64), nullable=True)    # MD5/SHA256 для проверки целостности

    __table_args__ = (
        Index("idx_documents_entity", "entity_type", "entity_id"),
        Index("idx_documents_uploaded_by", "uploaded_by"),
        Index("idx_documents_uploaded_at", "uploaded_at"),
        Index("idx_documents_type", "document_type"),
        Index("idx_documents_category", "category"),
    )

    # Relationships
    uploader = relationship("User", foreign_keys=[uploaded_by])

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename='{self.filename}', type='{self.document_type}')>"
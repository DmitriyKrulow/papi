# src/infrastructure/db/models/document_link.py
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from . import Base


class DocumentLink(Base):
    """Связь документа с активом (многие-ко-многим).
    Один документ может быть привязан к нескольким активам,
    один актив может иметь несколько документов.
    Документ удаляется физически только когда нет ни одной ссылки на него.
    """
    __tablename__ = "document_links"

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    linked_at = Column(DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        UniqueConstraint("document_id", "asset_id", name="uq_document_asset"),
        Index("idx_document_links_document_id", "document_id"),
        Index("idx_document_links_asset_id", "asset_id"),
    )

    document = relationship("Document", back_populates="asset_links")
    asset = relationship("Asset", back_populates="document_links")

    def __repr__(self) -> str:
        return f"<DocumentLink(id={self.id}, document_id={self.document_id}, asset_id={self.asset_id})>"
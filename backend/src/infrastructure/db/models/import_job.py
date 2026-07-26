from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from . import Base
from src.core.entities.import_job import ImportStatus, ImportType


class ImportJob(Base):
    """Модель задачи импорта данных"""
    __tablename__ = "import_jobs"

    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    import_type = Column(String(50), nullable=False)
    
    status = Column(String(50), nullable=False, default="pending")
    
    total_rows = Column(Integer, nullable=False, default=0)
    processed_rows = Column(Integer, nullable=False, default=0)
    successful_rows = Column(Integer, nullable=False, default=0)
    failed_rows = Column(Integer, nullable=False, default=0)
    
    errors = Column(JSON, nullable=True)
    error_file_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    result_file_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    summary = Column(JSON, nullable=True)
    
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    parameters = Column(JSON, nullable=True)
    
    __table_args__ = (
        Index("idx_import_jobs_status", "status"),
        Index("idx_import_jobs_created_by", "created_by"),
        Index("idx_import_jobs_created_at", "created_at"),
    )

    # Relationships
    created_by_user = relationship("User", foreign_keys=[created_by])
    error_document = relationship("Document", foreign_keys=[error_file_id])
    result_document = relationship("Document", foreign_keys=[result_file_id])

    def __repr__(self) -> str:
        return f"<ImportJob(id={self.id}, filename='{self.filename}', type='{self.import_type}', status='{self.status}')>"

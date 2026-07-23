from datetime import datetime
from typing import Optional

from sqlalchemy import (
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

from backend.src.core.entities.import_job import ImportStatus, ImportType

Base = declarative_base()


class ImportJob(Base):
    """Модель задачи импорта"""
    __tablename__ = "import_jobs"

    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    import_type = Column(
        Enum(ImportType, name="import_type_enum"),
        nullable=False,
        default=ImportType.ASSETS,
    )
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    status = Column(
        Enum(ImportStatus, name="import_status_enum"),
        nullable=False,
        default=ImportStatus.PENDING,
    )
    total_rows = Column(Integer, nullable=False, default=0)
    processed_rows = Column(Integer, nullable=False, default=0)
    successful_rows = Column(Integer, nullable=False, default=0)
    failed_rows = Column(Integer, nullable=False, default=0)

    errors = Column(Text, nullable=True)
    error_file_id = Column(Integer, nullable=True)
    result_file_id = Column(Integer, nullable=True)
    summary = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.now)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    parameters = Column(Text, nullable=True)

    __table_args__ = (
        Index("idx_import_jobs_status", "status"),
        Index("idx_import_jobs_import_type", "import_type"),
        Index("idx_import_jobs_created_by", "created_by"),
        Index("idx_import_jobs_created_at", "created_at"),
    )

    # Relationships
    created_by_user = relationship("User", backref="import_jobs")

    def __repr__(self) -> str:
        return f"<ImportJob(id={self.id}, filename='{self.filename}', type='{self.import_type.value}', status='{self.status.value}')>"

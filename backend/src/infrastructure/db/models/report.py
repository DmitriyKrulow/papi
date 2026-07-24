# src/infrastructure/db/models/report.py
from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    JSON,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Report(Base):
    """Модель отчета"""
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    report_type = Column(String(50), nullable=False)
    format = Column(String(20), nullable=False)  # pdf, excel, csv, html, json

    # Параметры и фильтры (JSON)
    parameters = Column(JSON, nullable=True)
    filters = Column(JSON, nullable=True)

    status = Column(String(20), nullable=False, default="generating")
    error_message = Column(Text, nullable=True)

    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    file_path = Column(String(500), nullable=True)  # Путь к сгенерированному файлу

    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    generated_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # Список тегов

    __table_args__ = (
        Index("idx_reports_type", "report_type"),
        Index("idx_reports_status", "status"),
        Index("idx_reports_created_by", "created_by"),
        Index("idx_reports_created_at", "created_at"),
        Index("idx_reports_period", "period_start", "period_end"),
    )

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    document = relationship("Document", foreign_keys=[document_id])

    def __repr__(self) -> str:
        return f"<Report(id={self.id}, name='{self.name}', type='{self.report_type}', status='{self.status}')>"
# backend/src/infrastructure/db/models/repair_template.py
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Boolean,
    JSON,
)
from sqlalchemy.orm import relationship
from . import Base


class RepairTemplate(Base):
    __tablename__ = "repair_templates"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    template_data = Column(JSON, nullable=False)  # Хранит структуру шаблона

    is_active = Column(Boolean, nullable=False, default=True)
    is_default = Column(Boolean, nullable=False, default=False)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        Index("idx_repair_templates_name", "name"),
        Index("idx_repair_templates_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<RepairTemplate(id={self.id}, name='{self.name}')>"
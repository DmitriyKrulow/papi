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
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Department(Base):
    """?????? ?????????????/??????"""
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False, unique=True, index=True)

    parent_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    head = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)

    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )

    __table_args__ = (
        Index("idx_departments_code", "code"),
        Index("idx_departments_parent_id", "parent_id"),
        Index("idx_departments_created_at", "created_at"),
    )

    # Self-referential relationship for hierarchy
    parent = relationship("Department", remote_side=[id], backref="subdepartments")

    # Relationships
    users = relationship("User", back_populates="department")
    created_assets = relationship(
        "Asset", back_populates="department_asset", foreign_keys="[Asset.department_code]"
    )

    def __repr__(self) -> str:
        return f"<Department(id={self.id}, name='{self.name}', code='{self.code}')>"



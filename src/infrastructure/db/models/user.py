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


class User(Base):
    """Модель пользователя системы"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    full_name = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)

    password_hash = Column(String(255), nullable=True)

    role = Column(String(50), nullable=False, default="user")
    is_active = Column(Boolean, nullable=False, default=True)

    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )

    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_username", "username"),
        Index("idx_users_department_id", "department_id"),
        Index("idx_users_created_at", "created_at"),
    )

    department = relationship("Department", back_populates="users")
    created_assets = relationship(
        "Asset",
        back_populates="created_by_user",
        foreign_keys="[Asset.created_by]",
    )
    updated_assets = relationship(
        "Asset",
        back_populates="updated_by_user",
        foreign_keys="[Asset.updated_by]",
    )
    repair_requests = relationship(
        "RepairRequest",
        back_populates="created_by_user",
        foreign_keys="[RepairRequest.created_by]",
    )
    assigned_repairs = relationship(
        "RepairRequest",
        back_populates="assigned_to_user",
        foreign_keys="[RepairRequest.assigned_to]",
    )
    documents = relationship(
        "Document",
        back_populates="uploaded_by_user",
        foreign_keys="[Document.uploaded_by]",
    )
    employees = relationship(
        "Employee", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

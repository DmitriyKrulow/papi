from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Employee(Base):
    """Модель сотрудника"""
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)

    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)

    position = Column(String(255), nullable=True)
    position_code = Column(String(50), nullable=True)

    employee_number = Column(String(50), nullable=True, unique=True)
    hire_date = Column(Date, nullable=True)
    termination_date = Column(Date, nullable=True)

    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )

    __table_args__ = (
        Index("idx_employees_department_id", "department_id"),
        Index("idx_employees_user_id", "user_id"),
        Index("idx_employees_hire_date", "hire_date"),
        Index("idx_employees_created_at", "created_at"),
    )

    # Relationships
    department = relationship("Department", back_populates="employees")
    user = relationship("User", back_populates="employees")

    def __repr__(self) -> str:
        return f"<Employee(id={self.id}, name='{self.last_name} {self.first_name}', position='{self.position}')>"

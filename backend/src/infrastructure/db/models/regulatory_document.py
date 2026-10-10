# backend/src/infrastructure/db/models/regulatory_document.py
"""Модель нормативных документов — оснащение, должностные обязанности, ответственность"""
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
from sqlalchemy.orm import relationship
from . import Base


class RegulatoryDocument(Base):
    """
    Нормативный документ.
    
    Типы документов:
    - equipment_standard: Норматив оснащения (сколько ПК на сотрудника)
    - job_description: Должностная инструкция (что должен делать сотрудник)
    - responsibility: Ответственность за пропажу/хищение
    - inventory_procedure: Порядок проведения инвентаризации
    - disposal_procedure: Порядок списания имущества
    """
    __tablename__ = "regulatory_documents"

    id = Column(Integer, primary_key=True)
    
    # Название документа
    title = Column(String(500), nullable=False)
    
    # Тип документа
    doc_type = Column(String(50), nullable=False, index=True)
    # equipment_standard, job_description, responsibility, inventory_procedure, disposal_procedure
    
    # Номер и дата
    document_number = Column(String(100), nullable=True)
    document_date = Column(DateTime, nullable=True)
    
    # Сфера применения
    applies_to_type = Column(String(50), nullable=True)  # должность, подразделение, тип актива
    applies_to_id = Column(Integer, nullable=True)  # ID сотрудника/подразделения/должности
    
    # Текст документа
    content = Column(Text, nullable=True)
    
    # Файл документа
    file_path = Column(String(500), nullable=True)
    file_name = Column(String(255), nullable=True)
    
    # Статус
    is_active = Column(Boolean, nullable=False, default=True)
    is_published = Column(Boolean, nullable=False, default=False)
    
    # Автор
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index("idx_regulatory_documents_doc_type", "doc_type"),
        Index("idx_regulatory_documents_applies_to", "applies_to_type", "applies_to_id"),
        Index("idx_regulatory_documents_is_active", "is_active"),
    )
    
    author = relationship("User", foreign_keys=[author_id])
    
    def __repr__(self) -> str:
        return f"<RegulatoryDocument(id={self.id}, title='{self.title}', type='{self.doc_type}')>"


class EquipmentStandard(Base):
    """
    Норматив оснащения по должностям.
    
    Пример:
    - Директор: 1 ПК + 1 монитор + 1 телефон
    - Менеджер: 1 ПК + 1 монитор + 1 наушники
    - Охранник: 1 рация + 1 фонарь
    """
    __tablename__ = "equipment_standards"

    id = Column(Integer, primary_key=True)
    
    # Должность / категория
    position_code = Column(String(100), nullable=False, index=True)
    position_name = Column(String(255), nullable=False)
    
    # Тип актива и количество
    asset_type_code = Column(String(50), nullable=False)
    asset_type_name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    
    # Описание
    description = Column(Text, nullable=True)
    
    # Приоритет (1 = обязательный, 2 = желательный)
    priority = Column(Integer, nullable=False, default=1)
    
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    
    __table_args__ = (
        Index("idx_equipment_standards_position", "position_code", "asset_type_code"),
    )
    
    def __repr__(self) -> str:
        return (
            f"<EquipmentStandard(id={self.id}, position='{self.position_name}', "
            f"type='{self.asset_type_name}', qty={self.quantity})>"
        )


class ResponsibilityRecord(Base):
    """
    Запись ответственности за имущество.
    
    Фиксирует:
    - Кто ответственный (МОЛ)
    - За какое подразделение/имущество
    - Уровень ответственности
    - Дата назначения
    """
    __tablename__ = "responsibility_records"

    id = Column(Integer, primary_key=True)
    
    # Сотрудник (МОЛ)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    
    # Подразделение
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)
    
    # Тип ответственности
    responsibility_type = Column(String(50), nullable=False)
    # full — за всё подразделение, partial — за часть, specific — за конкретные активы
    
    # Конкретные активы (если responsibility_type = specific)
    asset_ids = Column(Text, nullable=True)  # JSON: [1, 2, 3]
    
    # Уровень ответственности
    responsibility_level = Column(String(50), nullable=False)
    # full — полная материальная, limited — ограниченная, none — нет
    
    # Дата назначения
    assigned_date = Column(DateTime, nullable=False, default=datetime.now)
    
    # Дата окончания (если временно)
    end_date = Column(DateTime, nullable=True)
    
    # Статус
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Основание (приказ, договор)
    document_number = Column(String(100), nullable=True)
    document_date = Column(DateTime, nullable=True)
    
    # Комментарий
    comment = Column(Text, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    
    __table_args__ = (
        Index("idx_responsibility_employee", "employee_id"),
        Index("idx_responsibility_department", "department_id"),
        Index("idx_responsibility_is_active", "is_active"),
    )
    
    employee = relationship("Employee")
    department = relationship("Department")
    
    def __repr__(self) -> str:
        return (
            f"<ResponsibilityRecord(id={self.id}, employee={self.employee_id}, "
            f"type='{self.responsibility_type}', level='{self.responsibility_level}')>"
        )

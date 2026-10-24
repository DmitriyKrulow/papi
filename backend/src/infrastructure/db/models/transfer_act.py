# backend/src/infrastructure/db/models/transfer_act.py
"""Модель акта передачи имущества в пользование сотруднику"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from . import Base


class TransferAct(Base):
    """Акт передачи имущества сотруднику под роспись.

    Формируется отдельно от кабинетных описей: в акт можно включить
    произвольные активы (флешки, токены, ЭЦП, инструмент, сумки,
    расходники и т.п.) и передать их конкретному сотруднику.
    """
    __tablename__ = "transfer_acts"

    id = Column(Integer, primary_key=True)
    act_number = Column(String(50), nullable=False, index=True)
    act_date = Column(DateTime, nullable=False, default=datetime.now)

    # Сотрудник, которому передаётся имущество
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    employee_name = Column(String(255), nullable=True)
    employee_position = Column(String(255), nullable=True)

    # Подразделение / кабинет (опционально)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    department_name = Column(String(255), nullable=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True)
    room_name = Column(String(255), nullable=True)

    # Список id активов, включённых в акт (JSON)
    asset_ids = Column(JSON, nullable=False, default=list)
    
    # Список id единиц актива, включённых в акт (JSON) — для активов с quantity > 1
    unit_ids = Column(JSON, nullable=False, default=list)

    # Сгенерированный файл акта
    file_path = Column(String(500), nullable=True)

    # Скан-копии расписок (JSON: [{id, filename, file_path, uploaded_at}])
    attachments = Column(JSON, nullable=False, default=list)

    # Статус подписания
    signed = Column(Boolean, nullable=False, default=False)
    signed_at = Column(DateTime, nullable=True)
    signed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Архивация
    is_archived = Column(Boolean, nullable=False, default=False, server_default="false")
    archived_at = Column(DateTime, nullable=True)

    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        Index("idx_transfer_acts_act_number", "act_number"),
        Index("idx_transfer_acts_employee_id", "employee_id"),
        Index("idx_transfer_acts_signed", "signed"),
        Index("idx_transfer_acts_is_archived", "is_archived"),
        Index("idx_transfer_acts_created_at", "created_at"),
    )

    employee = relationship("Employee", foreign_keys=[employee_id])
    department = relationship("Department", foreign_keys=[department_id])
    room = relationship("Room", foreign_keys=[room_id])
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    signed_by_user = relationship("User", foreign_keys=[signed_by_user_id])

    def __repr__(self) -> str:
        return f"<TransferAct(id={self.id}, number='{self.act_number}', signed={self.signed})>"
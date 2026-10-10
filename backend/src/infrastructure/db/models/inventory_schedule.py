# backend/src/infrastructure/db/models/inventory_schedule.py
"""Модель расписания инвентаризаций — выборочная проверка по зонам"""
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


class InventorySchedule(Base):
    """
    Расписание проверок и инвентаризаций.
    
    Поддерживает различные типы проверок:
    - room: проверка помещений (инвентаризация)
    - flash_drive: проверка флеш-накопителей
    - token: проверка электронных токенов
    - signature: проверка электронных подписей (ЭЦП)
    - seal_stamp: проверка печатей и штампов
    - vehicle: проверка автомобилей
    - fire_extinguisher: проверка огнетушителей
    - ppe: проверка средств индивидуальной защиты (СИЗ)
    - security_drill: учения по информационной безопасности
    - fire_safety: учения по пожарной безопасности
    - employee_appearance: проверка внешнего вида сотрудников
    
    Автоматическое формирование графика:
    - За 6 месяцев проверяются все помещения/объекты
    - Админ может сдвигать даты вручную
    """
    __tablename__ = "inventory_schedules"

    id = Column(Integer, primary_key=True)
    
    # Название проверки
    name = Column(String(255), nullable=False)
    
    # Категория проверки (основная группировка)
    check_category = Column(String(50), nullable=False, default="room")
    # room, it_assets, safety, personnel, compliance
    
    # Тип проверки (детальный)
    check_type = Column(String(50), nullable=False, default="room")
    # room, flash_drive, token, signature, seal_stamp, vehicle,
    # fire_extinguisher, ppe, security_drill, fire_safety, employee_appearance
    
    # ID объекта проверки
    target_id = Column(Integer, nullable=True)
    target_type = Column(String(50), nullable=True)  # room, department, global
    
    # Название объекта
    target_name = Column(String(255), nullable=True)
    
    # Периодичность
    frequency = Column(String(50), nullable=False, default="semi_annual")
    # semi_annual, quarterly, monthly, biannual, custom
    
    # Даты
    scheduled_date = Column(DateTime, nullable=False, index=True)
    completed_date = Column(DateTime, nullable=True)
    
    # Статус
    status = Column(String(50), nullable=False, default="scheduled")
    # scheduled, in_progress, completed, cancelled, overdue
    
    # Ответственный
    responsible_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Связь с реальной инвентаризацией
    inventory_check_id = Column(Integer, nullable=True)
    
    # Уведомления
    notification_sent = Column(Boolean, nullable=False, default=False)
    reminder_sent = Column(Boolean, nullable=False, default=False)
    
    # Комментарий
    comment = Column(Text, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index("idx_inventory_schedules_scheduled_date", "scheduled_date"),
        Index("idx_inventory_schedules_status", "status"),
        Index("idx_inventory_schedules_target", "target_type", "target_id"),
        Index("idx_inventory_schedules_responsible", "responsible_id"),
    )
    
    responsible = relationship("User", foreign_keys=[responsible_id])
    
    def __repr__(self) -> str:
        return (
            f"<InventorySchedule(id={self.id}, name='{self.name}', "
            f"status='{self.status}', date={self.scheduled_date})>"
        )


class ReconciliationRecord(Base):
    """
    Запись ежемесячной сверки с бухгалтерией.
    
    Цель: ежемесячное сравнение данных реестра с бухгалтерским учётом.
    """
    __tablename__ = "reconciliation_records"

    id = Column(Integer, primary_key=True)
    
    # Период сверки (год-месяц)
    period_year = Column(Integer, nullable=False, index=True)
    period_month = Column(Integer, nullable=False, index=True)
    
    # Дата сверки
    reconciliation_date = Column(DateTime, nullable=False)
    
    # Данные из системы PAPI
    papi_total_assets = Column(Integer, nullable=False, default=0)
    papi_total_value = Column(Text, nullable=True)  # JSON: {"purchase": 100000, "current": 80000}
    
    # Данные из бухгалтерии
    accounting_total_assets = Column(Integer, nullable=True)
    accounting_total_value = Column(Text, nullable=True)  # JSON
    
    # Расхождения
    discrepancy_count = Column(Integer, nullable=False, default=0)
    discrepancy_value = Column(Text, nullable=True)  # JSON: {"missing": 5000, "surplus": 2000}
    
    # Статус
    status = Column(String(50), nullable=False, default="pending")
    # pending, in_progress, completed, discrepancies_found
    
    # Кто сверял
    reconciled_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Комментарий
    comment = Column(Text, nullable=True)
    
    # Файл отчёта
    report_file = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    
    __table_args__ = (
        Index("idx_reconciliation_period", "period_year", "period_month"),
        Index("idx_reconciliation_status", "status"),
    )
    
    reconciled_by_user = relationship("User", foreign_keys=[reconciled_by])
    
    def __repr__(self) -> str:
        return (
            f"<ReconciliationRecord(id={self.id}, period={self.period_year}-{self.period_month:02d}, "
            f"status='{self.status}')>"
        )

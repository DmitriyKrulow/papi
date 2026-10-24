# backend/src/infrastructure/db/models/asset_transfer_history.py
"""История передачи активов сотрудникам (по кабинетным описям и актам передачи)"""
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from . import Base


class AssetTransferHistory(Base):
    """Запись о передаче актива конкретному сотруднику.

    Источник (source):
      - 'inventory_print' — проставление сотрудника при подписании кабинетной описи;
      - 'transfer_act'    — проставление сотрудника при подписании акта передачи.
    """
    __tablename__ = "asset_transfer_history"

    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    
    # Если актив имеет несколько единиц (quantity > 1), указываем конкретную единицу
    asset_unit_id = Column(
        Integer, ForeignKey("asset_units.id"), nullable=True, index=True
    )

    # Кому было передано
    new_employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    new_employee_name = Column(String(255), nullable=True)

    # Прежний сотрудник (был до передачи)
    prev_employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    prev_employee_name = Column(String(255), nullable=True)

    # Источник: inventory_print | transfer_act
    source = Column(String(30), nullable=False, index=True)
    source_id = Column(Integer, nullable=True)
    source_ref = Column(String(255), nullable=True)

    transfer_date = Column(DateTime, nullable=False, default=datetime.now)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        Index("idx_asset_transfer_history_asset_id", "asset_id"),
        Index("idx_asset_transfer_history_new_employee_id", "new_employee_id"),
        Index("idx_asset_transfer_history_source", "source"),
        Index("idx_asset_transfer_history_transfer_date", "transfer_date"),
        Index("idx_asset_transfer_history_asset_unit_id", "asset_unit_id"),
    )

    asset = relationship("Asset", foreign_keys=[asset_id])
    asset_unit = relationship("AssetUnit", foreign_keys=[asset_unit_id])
    new_employee = relationship("Employee", foreign_keys=[new_employee_id])
    prev_employee = relationship("Employee", foreign_keys=[prev_employee_id])
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])

    def __repr__(self) -> str:
        return (
            f"<AssetTransferHistory(id={self.id}, asset={self.asset_id}, "
            f"to={self.new_employee_name}, source={self.source})>"
        )
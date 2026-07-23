# src/core/value_objects/status.py
from dataclasses import dataclass
from datetime import date as DateType  # Переименовываем импорт, чтобы избежать конфликта
from enum import Enum
from typing import Optional


class AssetStatus(Enum):
    """Статус актива"""
    ACTIVE = "active"               # В эксплуатации
    MAINTENANCE = "maintenance"     # На ремонте/ТО
    RESERVED = "reserved"           # В резерве
    DECOMMISSIONED = "decommissioned"  # Выведен из эксплуатации
    LOST = "lost"                   # Утерян
    WRITTEN_OFF = "written_off"     # Списан


@dataclass(frozen=True)
class Status:
    """
    Value Object для статуса актива.
    """
    value: AssetStatus
    reason: Optional[str] = None    # Причина (для списания и т.д.)
    changed_at: Optional[DateType] = None     # Дата изменения статуса (переименовано)
    
    def is_active(self) -> bool:
        return self.value == AssetStatus.ACTIVE
    
    def can_operate(self) -> bool:
        """Может ли актив использоваться"""
        return self.value in (AssetStatus.ACTIVE, AssetStatus.RESERVED)
    
    def is_available(self) -> bool:
        """Доступен ли актив для использования"""
        return self.value == AssetStatus.ACTIVE
    
    def is_written_off(self) -> bool:
        """Списан ли актив"""
        return self.value == AssetStatus.WRITTEN_OFF
    
    def is_maintenance(self) -> bool:
        """Находится ли актив на ремонте/ТО"""
        return self.value == AssetStatus.MAINTENANCE
    
    def is_reserved(self) -> bool:
        """Находится ли актив в резерве"""
        return self.value == AssetStatus.RESERVED
    
    def is_lost(self) -> bool:
        """Утерян ли актив"""
        return self.value == AssetStatus.LOST
    
    def is_decommissioned(self) -> bool:
        """Выведен ли из эксплуатации"""
        return self.value == AssetStatus.DECOMMISSIONED
    
    # Фабричные методы для создания статусов с датой
    
    @classmethod
    def active(cls, reason: Optional[str] = None) -> 'Status':
        """Создает статус 'В эксплуатации'"""
        return cls(AssetStatus.ACTIVE, reason, DateType.today())
    
    @classmethod
    def maintenance(cls, reason: Optional[str] = None) -> 'Status':
        """Создает статус 'На ремонте/ТО'"""
        return cls(AssetStatus.MAINTENANCE, reason, DateType.today())
    
    @classmethod
    def reserved(cls, reason: Optional[str] = None) -> 'Status':
        """Создает статус 'В резерве'"""
        return cls(AssetStatus.RESERVED, reason, DateType.today())
    
    @classmethod
    def decommissioned(cls, reason: Optional[str] = None) -> 'Status':
        """Создает статус 'Выведен из эксплуатации'"""
        return cls(AssetStatus.DECOMMISSIONED, reason, DateType.today())
    
    @classmethod
    def lost(cls, reason: Optional[str] = None) -> 'Status':
        """Создает статус 'Утерян'"""
        return cls(AssetStatus.LOST, reason, DateType.today())
    
    @classmethod
    def written_off(cls, reason: Optional[str] = None) -> 'Status':
        """Создает статус 'Списан'"""
        return cls(AssetStatus.WRITTEN_OFF, reason, DateType.today())
    
    def __str__(self) -> str:
        return self.value.value
    
    def __repr__(self) -> str:
        return f"Status(value={self.value}, reason='{self.reason}', changed_at={self.changed_at})"
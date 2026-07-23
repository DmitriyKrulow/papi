# src/core/entities/organization.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

from backend.src.core.value_objects import Phone, Email, Coordinates


@dataclass
class Organization:
    """Сущность "Организация/Предприятие" """
    id: int
    name: str
    short_name: Optional[str] = None
    inn: Optional[str] = None          # ИНН
    kpp: Optional[str] = None          # КПП
    ogrn: Optional[str] = None         # ОГРН
    
    # Контакты
    phone: Optional[Phone] = None
    email: Optional[Email] = None
    website: Optional[str] = None
    address: Optional[str] = None
    coordinates: Optional[Coordinates] = None
    
    # Юридическая информация
    legal_address: Optional[str] = None
    director: Optional[str] = None
    chief_accountant: Optional[str] = None
    
    # Статус
    is_active: bool = True
    
    # Метаданные
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def get_full_name(self) -> str:
        """Полное наименование"""
        return self.name
    
    def get_short_name(self) -> str:
        """Краткое наименование"""
        return self.short_name or self.name
    
    def __str__(self) -> str:
        return f"Organization(id={self.id}, name='{self.name}')"
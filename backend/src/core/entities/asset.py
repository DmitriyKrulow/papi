# src/core/entities/asset.py
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Tuple

from backend.src.core.value_objects import (
    InventoryNumber,
    BatchId,
    SerialNumber,
    YearPeriod,
    AssetType,
    AssetCategory,
    Status,
    AssetStatus,
    Money,
    Coordinates,
    Phone,
)


@dataclass
class Asset:
    """
    Сущность "Актив/Основное средство".
    Содержит бизнес-логику и правила для управления активами.
    """
    # ========== Идентификаторы ==========
    id: int
    inventory_number: InventoryNumber
    
    # ========== Извлеченные из номера компоненты ==========
    batch_id: Optional[BatchId] = None
    serial_number: Optional[SerialNumber] = None
    year_period: Optional[YearPeriod] = None
    asset_type: Optional[AssetType] = None
    
    # ========== Основная информация ==========
    name: str = ""
    description: str = ""
    model: str = ""
    
    # ========== Производитель ==========
    manufacturer_code: Optional[str] = None
    manufacturer_name: Optional[str] = None
    country_of_origin: Optional[str] = None
    
    # ========== Учетные данные ==========
    accounting_code: Optional[str] = None
    department_code: Optional[str] = None
    responsible_person: Optional[str] = None
    
    # ========== Финансовые данные ==========
    purchase_price: Optional[Money] = None
    current_value: Optional[Money] = None
    residual_value: Optional[Money] = None
    depreciation_rate: Optional[Decimal] = None  # в процентах
    
    # ========== Статус ==========
    status: Status = field(default_factory=lambda: Status(AssetStatus.ACTIVE))
    
    # ========== Локация ==========
    location: Optional[Coordinates] = None
    location_address: Optional[str] = None
    responsible_phone: Optional[Phone] = None
    
    # ========== Даты ==========
    purchase_date: Optional[date] = None
    commissioning_date: Optional[date] = None
    warranty_expiry: Optional[date] = None
    last_maintenance_date: Optional[date] = None
    next_maintenance_date: Optional[date] = None
    decommissioning_date: Optional[date] = None
    
    # ========== Метаданные ==========
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    
    # ========== Дополнительные атрибуты ==========
    tags: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    is_active: bool = True
    
    def __post_init__(self) -> None:
        """Валидация после инициализации"""
        if not self.name and not self.inventory_number:
            raise ValueError("Asset must have a name or inventory number")
        
        if self.purchase_price and self.purchase_price.amount < 0:
            raise ValueError("Purchase price cannot be negative")
        
        if self.current_value and self.current_value.amount < 0:
            raise ValueError("Current value cannot be negative")
        
        if self.depreciation_rate and (self.depreciation_rate < 0 or self.depreciation_rate > 100):
            raise ValueError("Depreciation rate must be between 0 and 100")
    
    # ========== Бизнес-методы ==========
    
    def change_status(self, new_status: Status) -> None:
        """Изменяет статус актива"""
        if self.status.is_written_off() and not new_status.is_written_off():
            raise ValueError("Cannot reactivate a written-off asset")
        
        # Если актив переводится в статус "Списан", устанавливаем дату списания
        if new_status.is_written_off():
            self.decommissioning_date = date.today()
        
        self.status = new_status
        self.updated_at = datetime.now()
    
    def update_value(self, new_value: Money) -> None:
        """Обновляет текущую стоимость актива"""
        if new_value.amount < 0:
            raise ValueError("Value cannot be negative")
        
        self.current_value = new_value
        self.updated_at = datetime.now()
    
    def calculate_depreciation(self) -> Optional[Money]:
        """
        Рассчитывает амортизацию за текущий период.
        Возвращает сумму амортизации.
        """
        if not self.current_value or not self.depreciation_rate:
            return None
        
        if self.status.is_written_off():
            return Money(Decimal('0.00'))
        
        depreciation_amount = self.current_value.amount * (self.depreciation_rate / 100)
        return Money(depreciation_amount)
    
    def apply_depreciation(self) -> Optional[Money]:
        """
        Применяет амортизацию и обновляет текущую стоимость.
        Возвращает сумму амортизации.
        """
        if not self.current_value:
            return None
            
        depreciation = self.calculate_depreciation()
        if not depreciation:
            return None
        
        new_value = self.current_value.amount - depreciation.amount
        if new_value < 0:
            new_value = Decimal('0.00')
        
        self.current_value = Money(new_value)
        self.updated_at = datetime.now()
        return depreciation
    
    def schedule_maintenance(self, maintenance_date: date) -> None:
        """Планирует следующее техническое обслуживание"""
        if maintenance_date < date.today():
            raise ValueError("Maintenance date cannot be in the past")
        
        self.next_maintenance_date = maintenance_date
        self.updated_at = datetime.now()
    
    def perform_maintenance(self) -> None:
        """Выполняет техническое обслуживание"""
        self.last_maintenance_date = date.today()
        self.updated_at = datetime.now()
    
    def transfer_to_department(self, department_code: str) -> None:
        """Перемещает актив в другое подразделение"""
        if not department_code:
            raise ValueError("Department code cannot be empty")
        
        self.department_code = department_code
        self.updated_at = datetime.now()
    
    def assign_responsible(self, person: str, phone: Optional[Phone] = None) -> None:
        """Назначает ответственное лицо"""
        if not person:
            raise ValueError("Responsible person cannot be empty")
        
        self.responsible_person = person
        if phone:
            self.responsible_phone = phone
        self.updated_at = datetime.now()
    
    def update_location(self, coordinates: Coordinates, address: Optional[str] = None) -> None:
        """Обновляет местоположение актива"""
        self.location = coordinates
        if address:
            self.location_address = address
        self.updated_at = datetime.now()
    
    # ========== Проверочные методы ==========
    
    def is_under_warranty(self) -> bool:
        """Проверяет, активна ли гарантия"""
        if not self.warranty_expiry:
            return False
        return date.today() <= self.warranty_expiry
    
    def get_age_years(self) -> Optional[int]:
        """Возвращает возраст актива в годах"""
        if not self.commissioning_date:
            return None
        today = date.today()
        return today.year - self.commissioning_date.year
    
    def get_age_months(self) -> Optional[int]:
        """Возвращает возраст актива в месяцах"""
        if not self.commissioning_date:
            return None
        today = date.today()
        return (today.year - self.commissioning_date.year) * 12 + (today.month - self.commissioning_date.month)
    
    def can_be_decommissioned(self) -> bool:
        """
        Проверяет, может ли актив быть списан.
        Условия:
        - Актив не списан
        - Актив старше 10 лет ИЛИ
        - Текущая стоимость ниже 1000 рублей
        - Актив не находится в статусе "На ремонте" или "В резерве"
        """
        if self.status.is_written_off():
            return False
        
        if self.status.is_maintenance() or self.status.is_reserved():
            return False
        
        # Если актив старше 10 лет
        age = self.get_age_years()
        if age and age >= 10:
            return True
        
        # Если стоимость ниже порога (1000 рублей)
        if self.current_value and self.current_value.amount < Decimal('1000.00'):
            return True
        
        return False
    
    def needs_maintenance(self) -> bool:
        """Проверяет, требуется ли техническое обслуживание"""
        if not self.next_maintenance_date:
            return False
        return date.today() >= self.next_maintenance_date
    
    def is_fully_depreciated(self) -> bool:
        """Проверяет, полностью ли самортизирован актив"""
        if not self.current_value:
            return False
        return self.current_value.amount == 0
    
    def is_available(self) -> bool:
        """Проверяет, доступен ли актив для использования"""
        return self.status.is_available() and not self.is_decommissioned()
    
    def is_decommissioned(self) -> bool:
        """Проверяет, выведен ли актив из эксплуатации"""
        return self.status.is_written_off() or self.status.is_decommissioned()
    
    # ========== Форматирование ==========
    
    def get_full_name(self) -> str:
        """Возвращает полное наименование актива"""
        parts = []
        if self.inventory_number:
            parts.append(f"[{self.inventory_number}]")
        if self.name:
            parts.append(self.name)
        if self.model:
            parts.append(f"({self.model})")
        return " ".join(parts)
    
    def get_summary(self) -> dict:
        """Возвращает краткую сводку по активу"""
        return {
            'id': self.id,
            'inventory_number': str(self.inventory_number),
            'name': self.name,
            'type': str(self.asset_type) if self.asset_type else None,
            'status': str(self.status),
            'current_value': str(self.current_value) if self.current_value else None,
            'age_years': self.get_age_years(),
            'under_warranty': self.is_under_warranty(),
            'needs_maintenance': self.needs_maintenance(),
            'is_available': self.is_available(),
        }
    
    def get_audit_trail(self) -> dict:
        """Возвращает информацию для аудита"""
        return {
            'id': self.id,
            'inventory_number': str(self.inventory_number),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'created_by': self.created_by,
            'updated_by': self.updated_by,
            'status_history': [
                {
                    'status': str(self.status),
                    'date': self.updated_at.isoformat(),
                }
            ],
        }
    
    # ========== Фабричные методы ==========
    
    @classmethod
    def create_from_inventory_number(
        cls,
        inventory_number: InventoryNumber,
        name: str = "",
        **kwargs
    ) -> 'Asset':
        """
        Создает актив на основе инвентарного номера с автоматическим извлечением данных.
        """
        # Извлекаем данные из инвентарного номера
        digits_only = inventory_number.digits_only
        
        # Извлекаем batch_id (первые 16 цифр)
        batch_id = None
        if len(digits_only) >= 16:
            try:
                batch_id = BatchId(digits_only[:16])
            except ValueError:
                pass
        
        # Извлекаем серийный номер (последние 4 цифры)
        serial_number = None
        if len(digits_only) >= 4:
            try:
                serial_number = SerialNumber.from_string(digits_only[-4:])
            except ValueError:
                pass
        
        # Извлекаем год
        year_period = YearPeriod.from_inventory_number(digits_only)
        
        # Определяем тип актива
        asset_type = AssetType.from_inventory_prefix(inventory_number.prefix)
        
        # Создаем актив
        return cls(
            id=kwargs.get('id', 0),
            inventory_number=inventory_number,
            batch_id=batch_id,
            serial_number=serial_number,
            year_period=year_period,
            asset_type=asset_type,
            name=name or f"Asset {inventory_number}",
            **{k: v for k, v in kwargs.items() if k not in [
                'id', 'inventory_number', 'batch_id', 
                'serial_number', 'year_period', 'asset_type', 'name'
            ]}
        )
    
    @classmethod
    def create_from_inventory_string(
        cls,
        inventory_string: str,
        name: str = "",
        **kwargs
    ) -> 'Asset':
        """
        Создает актив из строки инвентарного номера.
        """
        inventory_number = InventoryNumber(inventory_string)
        return cls.create_from_inventory_number(inventory_number, name, **kwargs)
    
    # ========== Специальные методы ==========
    
    def __str__(self) -> str:
        return f"Asset(id={self.id}, inventory={self.inventory_number}, name='{self.name}')"
    
    def __repr__(self) -> str:
        return (
            f"Asset(id={self.id}, inventory_number='{self.inventory_number}', "
            f"name='{self.name}', status={self.status}, "
            f"current_value={self.current_value})"
        )
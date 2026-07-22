# src/core/entities/depreciation_record.py
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, ClassVar, List

from src.core.value_objects import Money


class DepreciationMethod:
    """Константы методов амортизации"""
    LINEAR = "linear"
    DECLINING_BALANCE = "declining_balance"
    SUM_OF_YEARS = "sum_of_years"
    PRODUCTION = "production"
    
    @classmethod
    def get_all(cls) -> List[str]:
        """Возвращает все доступные методы"""
        return [
            cls.LINEAR,
            cls.DECLINING_BALANCE,
            cls.SUM_OF_YEARS,
            cls.PRODUCTION,
        ]
    
    @classmethod
    def get_display_name(cls, method: str) -> str:
        """Возвращает читаемое название метода"""
        names = {
            cls.LINEAR: "Линейный",
            cls.DECLINING_BALANCE: "Уменьшаемого остатка",
            cls.SUM_OF_YEARS: "По сумме чисел лет",
            cls.PRODUCTION: "Производственный",
        }
        return names.get(method, method)


@dataclass
class DepreciationRecord:
    """
    Сущность "Запись об амортизации".
    Хранит информацию о начисленной амортизации за период.
    """
    id: int
    asset_id: int
    period_start: date
    period_end: date
    depreciation_amount: Money
    accumulated_depreciation: Money
    book_value_before: Money
    book_value_after: Money
    rate: Decimal
    method: str
    
    # Поля со значениями по умолчанию
    created_at: datetime = field(default_factory=datetime.now)
    posted_at: Optional[datetime] = None
    posted_by: Optional[int] = None
    notes: Optional[str] = None
    document_number: Optional[str] = None
    
    _DAYS_IN_YEAR: ClassVar[int] = 365
    
    def __post_init__(self) -> None:
        """Валидация после инициализации"""
        if self.period_start > self.period_end:
            raise ValueError("Period start must be before period end")
        
        if self.rate < 0:
            raise ValueError("Depreciation rate cannot be negative")
        
        if self.rate > 100:
            raise ValueError("Depreciation rate cannot exceed 100%")
        
        if self.method not in DepreciationMethod.get_all():
            raise ValueError(f"Unknown depreciation method: {self.method}")
        
        # Проверка, что амортизация не превышает стоимость
        if self.depreciation_amount.amount > self.book_value_before.amount:
            raise ValueError("Depreciation amount cannot exceed book value")
        
        # Проверка, что book_value_after = book_value_before - depreciation_amount
        expected_after = self.book_value_before - self.depreciation_amount
        if expected_after.amount != self.book_value_after.amount:
            raise ValueError(
                f"Book value after mismatch: expected {expected_after}, got {self.book_value_after}"
            )
        
        # Проверка, что accumulated_depreciation >= depreciation_amount
        if self.accumulated_depreciation.amount < self.depreciation_amount.amount:
            raise ValueError("Accumulated depreciation cannot be less than current depreciation")
    
    def get_depreciation_yearly(self) -> Money:
        """Рассчитывает годовую сумму амортизации"""
        days = (self.period_end - self.period_start).days
        
        if days <= 0:
            return self.depreciation_amount
        
        if days >= self._DAYS_IN_YEAR:
            return self.depreciation_amount
        
        yearly_factor = Decimal(str(self._DAYS_IN_YEAR)) / Decimal(str(days))
        return self.depreciation_amount * yearly_factor
    
    def get_depreciation_monthly(self) -> Money:
        """Рассчитывает среднюю месячную сумму амортизации"""
        days = (self.period_end - self.period_start).days
        
        if days <= 0:
            return self.depreciation_amount
        
        monthly_factor = Decimal('30') / Decimal(str(days))
        return self.depreciation_amount * monthly_factor
    
    def get_depreciation_daily(self) -> Money:
        """Рассчитывает среднюю дневную сумму амортизации"""
        days = (self.period_end - self.period_start).days
        
        if days <= 0:
            return self.depreciation_amount
        
        return self.depreciation_amount / days
    
    def get_remaining_value(self) -> Money:
        """Возвращает оставшуюся стоимость актива после амортизации"""
        return self.book_value_after
    
    def get_depreciation_percentage(self) -> Decimal:
        """Возвращает процент амортизации от начальной стоимости"""
        if self.book_value_before.amount == 0:
            return Decimal('0')
        
        return (self.depreciation_amount.amount / self.book_value_before.amount) * 100
    
    def is_fully_depreciated(self) -> bool:
        """Проверяет, полностью ли самортизирован актив"""
        return self.book_value_after.amount == 0
    
    def post(self, posted_by: int) -> None:
        """Проводит запись в бухгалтерском учете"""
        if self.posted_at is not None:
            raise ValueError("Depreciation record already posted")
        
        self.posted_at = datetime.now()
        self.posted_by = posted_by
    
    def is_posted(self) -> bool:
        """Проверяет, проведена ли запись"""
        return self.posted_at is not None
    
    def get_period_days(self) -> int:
        """Возвращает количество дней в периоде"""
        return (self.period_end - self.period_start).days
    
    def get_period_months(self) -> float:
        """Возвращает количество месяцев в периоде"""
        days = self.get_period_days()
        return days / 30.44
    
    @property
    def period_days(self) -> int:
        """Количество дней в периоде"""
        return self.get_period_days()
    
    @property
    def method_display_name(self) -> str:
        """Читаемое название метода амортизации"""
        return DepreciationMethod.get_display_name(self.method)
    
    @property
    def rate_percent(self) -> str:
        """Ставка в процентах с символом %"""
        return f"{self.rate:.1f}%"
    
    def get_summary(self) -> dict:
        """Возвращает сводку по записи"""
        return {
            'id': self.id,
            'asset_id': self.asset_id,
            'period': f"{self.period_start} → {self.period_end}",
            'days': self.get_period_days(),
            'depreciation_amount': str(self.depreciation_amount),
            'book_value_before': str(self.book_value_before),
            'book_value_after': str(self.book_value_after),
            'accumulated_depreciation': str(self.accumulated_depreciation),
            'rate': self.rate_percent,
            'method': self.method_display_name,
            'fully_depreciated': self.is_fully_depreciated(),
            'is_posted': self.is_posted(),
        }
    
    def to_dict(self) -> dict:
        """Преобразует в словарь для сериализации"""
        return {
            'id': self.id,
            'asset_id': self.asset_id,
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat(),
            'depreciation_amount': float(self.depreciation_amount.amount),
            'accumulated_depreciation': float(self.accumulated_depreciation.amount),
            'book_value_before': float(self.book_value_before.amount),
            'book_value_after': float(self.book_value_after.amount),
            'rate': float(self.rate),
            'method': self.method,
            'created_at': self.created_at.isoformat(),
            'posted_at': self.posted_at.isoformat() if self.posted_at else None,
            'posted_by': self.posted_by,
            'notes': self.notes,
            'document_number': self.document_number,
        }
    
    def __str__(self) -> str:
        return (
            f"DepreciationRecord(id={self.id}, asset_id={self.asset_id}, "
            f"amount={self.depreciation_amount}, period={self.period_start}→{self.period_end})"
        )
    
    def __repr__(self) -> str:
        return (
            f"DepreciationRecord(id={self.id}, asset_id={self.asset_id}, "
            f"amount={self.depreciation_amount}, method='{self.method}', "
            f"posted={self.is_posted()})"
        )
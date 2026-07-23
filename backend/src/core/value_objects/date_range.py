# src/core/value_objects/date_range.py
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional, Iterator


@dataclass(frozen=True)
class DateRange:
    """
    Value Object для диапазона дат.
    """
    
    start_date: date
    end_date: date
    
    def __post_init__(self) -> None:
        """Валидация диапазона"""
        if self.start_date > self.end_date:
            raise ValueError(
                f"Start date ({self.start_date}) must be before end date ({self.end_date})"
            )
    
    # ========== Свойства ==========
    
    @property
    def days(self) -> int:
        """Количество дней в диапазоне (включая обе даты)"""
        return (self.end_date - self.start_date).days + 1
    
    @property
    def is_single_day(self) -> bool:
        """Проверяет, состоит ли диапазон из одного дня"""
        return self.start_date == self.end_date
    
    @property
    def is_future(self) -> bool:
        """Проверяет, является ли диапазон будущим"""
        today = date.today()
        return self.start_date > today
    
    @property
    def is_past(self) -> bool:
        """Проверяет, является ли диапазон прошлым"""
        today = date.today()
        return self.end_date < today
    
    @property
    def is_current(self) -> bool:
        """Проверяет, содержит ли диапазон сегодняшний день"""
        today = date.today()
        return self.start_date <= today <= self.end_date
    
    # ========== Методы ==========
    
    def contains(self, dt: date) -> bool:
        """Проверяет, входит ли дата в диапазон"""
        return self.start_date <= dt <= self.end_date
    
    def overlaps(self, other: 'DateRange') -> bool:
        """Проверяет, пересекаются ли диапазоны"""
        return not (self.end_date < other.start_date or other.end_date < self.start_date)
    
    def intersect(self, other: 'DateRange') -> Optional['DateRange']:
        """
        Возвращает пересечение двух диапазонов.
        Возвращает None, если пересечения нет.
        """
        if not self.overlaps(other):
            return None
        
        return DateRange(
            start_date=max(self.start_date, other.start_date),
            end_date=min(self.end_date, other.end_date)
        )
    
    def union(self, other: 'DateRange') -> Optional['DateRange']:
        """
        Возвращает объединение двух диапазонов.
        Возвращает None, если диапазоны не пересекаются или не соприкасаются.
        """
        if self.end_date + timedelta(days=1) < other.start_date:
            return None
        if other.end_date + timedelta(days=1) < self.start_date:
            return None
        
        return DateRange(
            start_date=min(self.start_date, other.start_date),
            end_date=max(self.end_date, other.end_date)
        )
    
    def iterate_dates(self) -> Iterator[date]:
        """Итератор по всем датам в диапазоне"""
        current = self.start_date
        while current <= self.end_date:
            yield current
            current += timedelta(days=1)
    
    def shift(self, days: int) -> 'DateRange':
        """Смещает диапазон на указанное количество дней"""
        return DateRange(
            start_date=self.start_date + timedelta(days=days),
            end_date=self.end_date + timedelta(days=days)
        )
    
    def split_by_months(self) -> list['DateRange']:
        """
        Разбивает диапазон на месячные интервалы.
        """
        ranges = []
        current = self.start_date
        
        while current <= self.end_date:
            # Первый день следующего месяца
            if current.month == 12:
                next_month = date(current.year + 1, 1, 1)
            else:
                next_month = date(current.year, current.month + 1, 1)
            
            month_end = min(next_month - timedelta(days=1), self.end_date)
            
            ranges.append(DateRange(
                start_date=current,
                end_date=month_end
            ))
            
            current = next_month
        
        return ranges
    
    # ========== Специальные методы ==========
    
    def __str__(self) -> str:
        return f"{self.start_date} → {self.end_date}"
    
    def __repr__(self) -> str:
        return f"DateRange(start={self.start_date}, end={self.end_date})"
# src/core/value_objects/money.py
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Union, Optional


@dataclass(frozen=True)
class Money:
    """
    Value Object для денежных сумм.
    Работает только в рублях (RUB).
    Поддерживает арифметические операции.
    """
    
    amount: Decimal
    currency: str = 'RUB'  # Фиксированно рубли
    
    def __post_init__(self) -> None:
        """Валидация суммы"""
        if self.amount < 0:
            raise ValueError(f"Amount cannot be negative: {self.amount}")
        
        if self.currency != 'RUB':
            raise ValueError(f"Only RUB currency is supported, got {self.currency}")
        
        # Округляем до 2 знаков после запятой
        rounded = self.amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        object.__setattr__(self, 'amount', rounded)
    
    # ========== Фабричные методы ==========
    
    @classmethod
    def from_int(cls, value: int) -> 'Money':
        """Создает из целого числа (рубли)"""
        return cls(Decimal(str(value)))
    
    @classmethod
    def from_float(cls, value: float) -> 'Money':
        """Создает из числа с плавающей точкой"""
        return cls(Decimal(str(value)))
    
    @classmethod
    def from_str(cls, value: str) -> 'Money':
        """Создает из строки"""
        return cls(Decimal(value))
    
    @classmethod
    def from_kopecks(cls, kopecks: int) -> 'Money':
        """Создает из копеек (целое число)"""
        return cls(Decimal(str(kopecks / 100)))
    
    @classmethod
    def zero(cls) -> 'Money':
        """Нулевая сумма"""
        return cls(Decimal('0'))
    
    # ========== Свойства ==========
    
    @property
    def kopecks(self) -> int:
        """Количество копеек (целое число)"""
        return int(self.amount * 100)
    
    @property
    def is_zero(self) -> bool:
        """Проверяет, является ли сумма нулевой"""
        return self.amount == Decimal('0')
    
    @property
    def is_positive(self) -> bool:
        """Проверяет, является ли сумма положительной"""
        return self.amount > 0
    
    # ========== Арифметические операции ==========
    
    def add(self, other: 'Money') -> 'Money':
        """Сложение двух сумм"""
        self._validate_currency(other)
        return Money(self.amount + other.amount)
    
    def subtract(self, other: 'Money') -> 'Money':
        """Вычитание двух сумм"""
        self._validate_currency(other)
        result = self.amount - other.amount
        if result < 0:
            raise ValueError("Cannot subtract to negative amount")
        return Money(result)
    
    def multiply(self, factor: Union[int, float, Decimal]) -> 'Money':
        """Умножение на число"""
        if isinstance(factor, (int, float)):
            factor = Decimal(str(factor))
        return Money(self.amount * factor)
    
    def divide(self, divisor: Union[int, float, Decimal]) -> 'Money':
        """Деление на число"""
        if isinstance(divisor, (int, float)):
            divisor = Decimal(str(divisor))
        if divisor == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        return Money(self.amount / divisor)
    
    def percent(self, percentage: Union[int, float, Decimal]) -> 'Money':
        """Вычисляет процент от суммы"""
        if isinstance(percentage, (int, float)):
            percentage = Decimal(str(percentage))
        return Money(self.amount * percentage / 100)
    
    def _validate_currency(self, other: 'Money') -> None:
        """Проверяет, что валюты совпадают"""
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot operate with different currencies: {self.currency} vs {other.currency}"
            )
    
    # ========== Магические методы для операторов ==========
    
    def __add__(self, other: 'Money') -> 'Money':
        """Поддержка оператора +"""
        if not isinstance(other, Money):
            return NotImplemented
        self._validate_currency(other)
        return Money(self.amount + other.amount)
    
    def __sub__(self, other: 'Money') -> 'Money':
        """Поддержка оператора -"""
        if not isinstance(other, Money):
            return NotImplemented
        self._validate_currency(other)
        result = self.amount - other.amount
        if result < 0:
            raise ValueError("Cannot subtract to negative amount")
        return Money(result)
    
    def __mul__(self, other: Union[int, float, Decimal]) -> 'Money':
        """Поддержка оператора * (умножение на число)"""
        if isinstance(other, (int, float)):
            factor = Decimal(str(other))
        elif isinstance(other, Decimal):
            factor = other
        else:
            return NotImplemented
        return Money(self.amount * factor)
    
    def __rmul__(self, other: Union[int, float, Decimal]) -> 'Money':
        """Поддержка оператора * (число * Money)"""
        return self.__mul__(other)
    
    def __truediv__(self, other: Union[int, float, Decimal]) -> 'Money':
        """Поддержка оператора / (деление на число)"""
        if isinstance(other, (int, float)):
            divisor = Decimal(str(other))
        elif isinstance(other, Decimal):
            divisor = other
        else:
            return NotImplemented
        if divisor == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        return Money(self.amount / divisor)
    
    def __eq__(self, other: object) -> bool:
        """Поддержка оператора =="""
        if not isinstance(other, Money):
            return False
        return self.amount == other.amount and self.currency == other.currency
    
    def __lt__(self, other: 'Money') -> bool:
        """Поддержка оператора <"""
        if not isinstance(other, Money):
            return NotImplemented
        self._validate_currency(other)
        return self.amount < other.amount
    
    def __le__(self, other: 'Money') -> bool:
        """Поддержка оператора <="""
        if not isinstance(other, Money):
            return NotImplemented
        self._validate_currency(other)
        return self.amount <= other.amount
    
    def __gt__(self, other: 'Money') -> bool:
        """Поддержка оператора >"""
        if not isinstance(other, Money):
            return NotImplemented
        self._validate_currency(other)
        return self.amount > other.amount
    
    def __ge__(self, other: 'Money') -> bool:
        """Поддержка оператора >="""
        if not isinstance(other, Money):
            return NotImplemented
        self._validate_currency(other)
        return self.amount >= other.amount
    
    def __neg__(self) -> 'Money':
        """Унарный минус (для отрицательных сумм)"""
        return Money(-self.amount)
    
    def __abs__(self) -> 'Money':
        """Абсолютное значение"""
        return Money(abs(self.amount))
    
    def __hash__(self) -> int:
        """Хеш для использования в словарях и множествах"""
        return hash((self.amount, self.currency))
    
    # ========== Методы форматирования ==========
    
    def format_rub(self) -> str:
        """Форматирует сумму в рубли с символом ₽"""
        return f"{self.amount:.2f} ₽"
    
    def format_no_symbol(self) -> str:
        """Форматирует сумму без символа валюты"""
        return f"{self.amount:.2f}"
    
    def format_kopecks(self) -> str:
        """Возвращает сумму в копейках как строку"""
        return f"{self.kopecks} коп."
    
    def format_with_words(self) -> str:
        """Форматирует сумму прописью (упрощенный вариант)"""
        rubles = int(self.amount)
        kopecks = int((self.amount % 1) * 100)
        
        rubles_word = self._number_to_words(rubles, 'рубль', 'рубля', 'рублей')
        kopecks_word = self._number_to_words(kopecks, 'копейка', 'копейки', 'копеек')
        
        return f"{rubles_word} {kopecks_word}"
    
    @staticmethod
    def _number_to_words(n: int, sing: str, plu2: str, plu5: str) -> str:
        """Вспомогательная функция для склонения"""
        if n % 100 in (11, 12, 13, 14):
            return f"{n} {plu5}"
        
        last = n % 10
        if last == 1:
            return f"{n} {sing}"
        elif last in (2, 3, 4):
            return f"{n} {plu2}"
        else:
            return f"{n} {plu5}"
    
    # ========== Специальные методы ==========
    
    def __str__(self) -> str:
        return self.format_rub()
    
    def __repr__(self) -> str:
        return f"Money(amount={self.amount}, currency='{self.currency}')"
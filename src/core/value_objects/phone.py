# src/core/value_objects/phone.py
import re
from dataclasses import dataclass
from typing import Optional, ClassVar, Pattern


@dataclass(frozen=True)
class Phone:
    """
    Value Object для телефонного номера.
    Поддерживает российские и международные форматы.
    """
    
    value: str
    
    # Регулярное выражение для российских номеров
    _RUSSIAN_PATTERN: ClassVar[Pattern] = re.compile(
        r'^(\+7|8)?[\s\-]?\(?(\d{3})\)?[\s\-]?(\d{3})[\s\-]?(\d{2})[\s\-]?(\d{2})$'
    )
    
    # Международный формат (любой номер)
    _INTERNATIONAL_PATTERN: ClassVar[Pattern] = re.compile(
        r'^\+\d{1,3}[\s\-]?\(?\d{1,4}\)?[\s\-]?\d{1,4}[\s\-]?\d{1,4}[\s\-]?\d{1,4}$'
    )
    
    def __post_init__(self) -> None:
        """Нормализация и валидация номера"""
        # Удаляем все пробелы и дефисы
        cleaned = re.sub(r'[\s\-\(\)]', '', self.value)
        
        # Если номер начинается с 8, заменяем на +7
        if cleaned.startswith('8') and len(cleaned) == 11:
            cleaned = '+7' + cleaned[1:]
        elif not cleaned.startswith('+'):
            # Если нет плюса, добавляем +7 для российских номеров
            if cleaned.startswith('7') and len(cleaned) == 11:
                cleaned = '+' + cleaned
            else:
                cleaned = '+' + cleaned
        
        object.__setattr__(self, 'value', cleaned)
        
        if not self._is_valid():
            raise ValueError(f"Invalid phone number: {self.value}")
    
    def _is_valid(self) -> bool:
        """Проверяет валидность номера"""
        # Убираем все не-цифры для проверки
        digits = re.sub(r'\D', '', self.value)
        
        # Минимальная длина номера
        if len(digits) < 10:
            return False
        
        # Проверка через регулярные выражения
        clean_for_check = re.sub(r'[\(\)\s\-]', '', self.value)
        return bool(
            self._RUSSIAN_PATTERN.match(clean_for_check) or
            self._INTERNATIONAL_PATTERN.match(self.value)
        )
    
    # ========== Свойства ==========
    
    @property
    def digits_only(self) -> str:
        """Возвращает только цифры номера"""
        return re.sub(r'\D', '', self.value)
    
    @property
    def country_code(self) -> str:
        """Возвращает код страны"""
        if self.value.startswith('+'):
            # Извлекаем код страны (до 3 цифр)
            match = re.match(r'^\+(\d{1,3})', self.value)
            return match.group(1) if match else ''
        return ''
    
    @property
    def national_number(self) -> str:
        """Возвращает номер без кода страны"""
        if self.value.startswith('+'):
            # Убираем код страны
            match = re.match(r'^\+(\d{1,3})(.*)$', self.value)
            return match.group(2) if match else self.value
        return self.value
    
    @property
    def is_russian(self) -> bool:
        """Проверяет, российский ли номер"""
        return self.country_code in ('7', '8')
    
    # ========== Методы ==========
    
    def format_e164(self) -> str:
        """Форматирует в E.164 (международный формат)"""
        return self.value
    
    def format_pretty(self) -> str:
        """Красивый формат для отображения"""
        digits = self.digits_only
        
        if self.is_russian and len(digits) == 11:
            # +7 (999) 123-45-67
            return f"+{digits[0]} ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
        elif len(digits) >= 10:
            # Международный формат
            country = digits[:self.country_code]
            rest = digits[len(self.country_code):]
            return f"+{country} {rest[:3]} {rest[3:6]} {rest[6:]}"
        
        return self.value
    
    def obfuscate(self) -> str:
        """Скрывает номер для логов"""
        digits = self.digits_only
        if len(digits) >= 10:
            return f"+{digits[0]}****{digits[-4:]}"
        return '***'
    
    def is_same(self, other: 'Phone') -> bool:
        """Сравнивает номера (игнорируя форматирование)"""
        return self.digits_only == other.digits_only
    
    # ========== Специальные методы ==========
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"Phone('{self.value}')"
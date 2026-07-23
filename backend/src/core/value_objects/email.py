import re
from dataclasses import dataclass
from typing import Optional, Tuple, ClassVar, Set


@dataclass(frozen=True)
class Email:
    """
    Value Object для email-адреса.
    Валидирует формат, нормализует и предоставляет методы для работы.
    """
    
    value: str
    
    # Используем ClassVar для констант класса
    _EMAIL_REGEX: ClassVar[re.Pattern] = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    _ALLOWED_TLDS: ClassVar[Set[str]] = {
        'com', 'ru', 'org', 'net', 'edu', 'gov', 'io', 'uk', 'de', 'fr', 'local'
    }
    
    def __post_init__(self) -> None:
        """Выполняется после инициализации (для dataclass)"""
        # Нормализуем значение (удаляем пробелы и приводим к нижнему регистру)
        normalized = self.value.strip().lower()
        
        # Для frozen dataclass используем object.__setattr__
        object.__setattr__(self, 'value', normalized)
        
        # Валидация
        if not self._is_valid_format(normalized):
            raise ValueError(f"Invalid email format: {self.value}")
        
        if not self._is_allowed_domain(normalized):
            domain = self._get_domain(normalized)
            raise ValueError(f"Domain not allowed: {domain}")
    
    # ========== Валидация ==========
    
    @classmethod
    def _is_valid_format(cls, email: str) -> bool:
        """Проверяет формат email через регулярное выражение"""
        return bool(cls._EMAIL_REGEX.match(email))
    
    @classmethod
    def _is_allowed_domain(cls, email: str) -> bool:
        """Проверяет, что домен верхнего уровня разрешен"""
        domain = cls._get_domain(email)
        if domain is None:
            return False
        
        tld = domain.split('.')[-1]
        return tld in cls._ALLOWED_TLDS
    
    @classmethod
    def _get_domain(cls, email: str) -> Optional[str]:
        """
        Извлекает доменную часть из email.
        Возвращает None, если домен не найден.
        """
        parts = email.split('@')
        if len(parts) != 2 or not parts[1]:
            return None
        return parts[1]
    
    @classmethod
    def _get_local_part(cls, email: str) -> Optional[str]:
        """Извлекает локальную часть из email."""
        parts = email.split('@')
        if len(parts) != 2 or not parts[0]:
            return None
        return parts[0]
    
    # ========== Публичные свойства ==========
    
    @property
    def domain(self) -> str:
        """
        Возвращает доменную часть.
        Гарантированно возвращает str, т.к. валидация уже прошла.
        """
        domain = self._get_domain(self.value)
        # Безопасное приведение: если None, значит email невалидный,
        # но мы уже проверили это в __post_init__
        return domain if domain is not None else ""
    
    @property
    def local_part(self) -> str:
        """
        Возвращает локальную часть (до @).
        Гарантированно возвращает str.
        """
        local = self._get_local_part(self.value)
        return local if local is not None else ""
    
    @property
    def is_gmail(self) -> bool:
        """Проверяет, является ли email gmail.com (игнорируя точки и +)"""
        domain = self.domain
        if domain not in ('gmail.com', 'googlemail.com'):
            return False
        
        local = self.local_part
        normalized_local = local.replace('.', '').split('+')[0]
        return bool(normalized_local)
    
    # ========== Публичные методы ==========
    
    def get_normalized_gmail(self) -> Optional['Email']:
        """
        Возвращает нормализованный Gmail-адрес (без точек и плюсов).
        Для не-Gmail адресов возвращает None.
        """
        if not self.is_gmail:
            return None
        
        local = self.local_part.replace('.', '').split('+')[0]
        return Email(f"{local}@gmail.com")
    
    def obfuscate(self) -> str:
        """
        Скрывает часть email для логов и отображения (защита персональных данных)
        """
        local = self.local_part
        domain = self.domain
        
        if not local or not domain:
            return self.value  # fallback
        
        if len(local) <= 3:
            hidden_local = local[0] + '***'
        else:
            hidden_local = local[:2] + '***' + local[-1]
        
        return f"{hidden_local}@{domain}"
    
    def is_same_domain(self, other: 'Email') -> bool:
        """Проверяет, принадлежат ли email-ы одному домену"""
        return self.domain == other.domain
    
    def is_organization_email(self, org_domains: Tuple[str, ...]) -> bool:
        """
        Проверяет, является ли email корпоративным (принадлежит организации)
        
        Пример:
            email.is_organization_email(('company.com', 'corp.net'))
        """
        return self.domain in org_domains
    
    # ========== Фабричные методы ==========
    
    @classmethod
    def create_allow_null(cls, value: Optional[str]) -> Optional['Email']:
        """
        Безопасное создание: возвращает None для пустых значений.
        Удобно при работе с опциональными полями БД.
        """
        if not value or not value.strip():
            return None
        return cls(value)
    
    @classmethod
    def create_quiet(cls, value: str) -> Optional['Email']:
        """
        Создает email без выбрасывания исключений.
        Возвращает None при ошибке валидации.
        """
        try:
            return cls(value)
        except ValueError:
            return None
    
    @classmethod
    def random(cls) -> 'Email':
        """Создает случайный email для тестирования"""
        import uuid
        return cls(f"test_{uuid.uuid4().hex[:8]}@test.com")
    
    # ========== Специальные методы ==========
    
    def __str__(self) -> str:
        """Строковое представление для пользователя"""
        return self.value
    
    def __repr__(self) -> str:
        """Отладочное представление"""
        return f"Email('{self.value}')"
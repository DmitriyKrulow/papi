# src/core/value_objects/password_hash.py
from dataclasses import dataclass
from typing import Optional
import hashlib
import secrets
import base64


@dataclass(frozen=True)
class PasswordHash:
    """
    Value Object для хеша пароля.
    Использует PBKDF2 с солью для безопасного хранения.
    """
    
    hash_value: str  # Хранится в формате: "salt$iterations$hash"
    
    # Параметры хеширования по умолчанию
    _DEFAULT_ITERATIONS: int = 100000
    _DEFAULT_SALT_LENGTH: int = 32
    _HASH_ALGORITHM: str = 'sha256'
    
    def __post_init__(self) -> None:
        """Валидация формата хеша"""
        parts = self.hash_value.split('$')
        if len(parts) != 3:
            raise ValueError("Invalid hash format. Expected: salt$iterations$hash")
        
        salt, iterations, _ = parts
        
        if not salt:
            raise ValueError("Salt cannot be empty")
        
        try:
            int(iterations)
        except ValueError:
            raise ValueError("Iterations must be a number")
    
    # ========== Фабричные методы ==========
    
    @classmethod
    def from_plain_password(cls, password: str) -> 'PasswordHash':
        """
        Создает хеш из обычного пароля.
        Генерирует случайную соль.
        """
        salt = secrets.token_bytes(cls._DEFAULT_SALT_LENGTH)
        salt_b64 = base64.b64encode(salt).decode('utf-8')
        
        hash_bytes = hashlib.pbkdf2_hmac(
            cls._HASH_ALGORITHM,
            password.encode('utf-8'),
            salt,
            cls._DEFAULT_ITERATIONS
        )
        hash_b64 = base64.b64encode(hash_bytes).decode('utf-8')
        
        return cls(f"{salt_b64}${cls._DEFAULT_ITERATIONS}${hash_b64}")
    
    @classmethod
    def from_hash_string(cls, hash_string: str) -> 'PasswordHash':
        """Создает объект из существующей строки хеша"""
        return cls(hash_string)
    
    @classmethod
    def random(cls) -> 'PasswordHash':
        """Создает случайный хеш для тестов"""
        return cls.from_plain_password(secrets.token_hex(16))
    
    # ========== Методы ==========
    
    def verify(self, password: str) -> bool:
        """
        Проверяет, соответствует ли пароль данному хешу.
        """
        parts = self.hash_value.split('$')
        salt_b64, iterations_str, stored_hash_b64 = parts
        iterations = int(iterations_str)
        
        salt = base64.b64decode(salt_b64)
        
        computed_hash_bytes = hashlib.pbkdf2_hmac(
            self._HASH_ALGORITHM,
            password.encode('utf-8'),
            salt,
            iterations
        )
        computed_hash_b64 = base64.b64encode(computed_hash_bytes).decode('utf-8')
        
        # Постоянное время сравнения (защита от timing attacks)
        return secrets.compare_digest(computed_hash_b64, stored_hash_b64)
    
    @property
    def is_empty(self) -> bool:
        """Проверяет, является ли хеш пустым (не рекомендуется использовать)"""
        return self.hash_value == '' or self.hash_value == '$$'
    
    # ========== Специальные методы ==========
    
    def __str__(self) -> str:
        return self.hash_value
    
    def __repr__(self) -> str:
        return f"PasswordHash('{self.hash_value[:20]}...')"
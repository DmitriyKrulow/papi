# src/core/entities/user.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from backend.src.core.value_objects import Email, Phone, PasswordHash


@dataclass
class User:
    """
    Сущность "Пользователь".
    Содержит бизнес-логику и правила для пользователя.
    """
    id: Optional[int] = None
    email: Optional[Email] = None
    username: str = ""
    full_name: Optional[str] = None
    phone: Optional[Phone] = None
    password_hash: Optional[PasswordHash] = None
    role: str = "user"
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self) -> None:
        """Валидация после инициализации"""
        if not self.username or len(self.username) < 3:
            raise ValueError("Username must be at least 3 characters")
        if self.username and len(self.username) > 50:
            raise ValueError("Username must be at most 50 characters")
        if self.full_name and len(self.full_name) > 100:
            raise ValueError("Full name must be at most 100 characters")
    
    # ========== Бизнес-методы ==========
    
    def change_email(self, new_email: Email) -> None:
        """Изменяет email пользователя"""
        if self.email == new_email:
            raise ValueError("New email must be different from current email")
        self.email = new_email
        self.updated_at = datetime.now()
    
    def change_phone(self, new_phone: Optional[Phone]) -> None:
        """Изменяет телефон пользователя"""
        if self.phone == new_phone:
            raise ValueError("New phone must be different from current phone")
        self.phone = new_phone
        self.updated_at = datetime.now()
    
    def change_password(self, new_password_hash: PasswordHash) -> None:
        """Изменяет пароль пользователя"""
        if self.password_hash == new_password_hash:
            raise ValueError("New password must be different from current password")
        self.password_hash = new_password_hash
        self.updated_at = datetime.now()
    
    def verify_password(self, plain_password: str) -> bool:
        """
        Проверяет, соответствует ли введенный пароль хешу.
        """
        if not self.password_hash:
            return False
        return self.password_hash.verify(plain_password)
    
    def activate(self) -> None:
        """Активирует пользователя"""
        if self.is_active:
            raise ValueError("User is already active")
        self.is_active = True
        self.updated_at = datetime.now()
    
    def deactivate(self) -> None:
        """Деактивирует пользователя"""
        if not self.is_active:
            raise ValueError("User is already inactive")
        self.is_active = False
        self.updated_at = datetime.now()
    
    def update_profile(
        self,
        username: Optional[str] = None,
        full_name: Optional[str] = None,
    ) -> None:
        """Обновляет профиль пользователя"""
        if username is not None:
            if len(username) < 3:
                raise ValueError("Username must be at least 3 characters")
            if len(username) > 50:
                raise ValueError("Username must be at most 50 characters")
            self.username = username.lower()
        
        if full_name is not None:
            if len(full_name) > 100:
                raise ValueError("Full name must be at most 100 characters")
            self.full_name = full_name
        
        self.updated_at = datetime.now()
    
    # ========== Свойства ==========
    
    @property
    def email_domain(self) -> str:
        """Возвращает домен email-адреса"""
        return self.email.domain
    
    @property
    def is_verified(self) -> bool:
        """Проверяет, верифицирован ли пользователь (есть ли телефон)"""
        return self.phone is not None
    
    @property
    def has_password(self) -> bool:
        """Проверяет, установлен ли пароль"""
        return self.password_hash is not None
    
    # ========== Специальные методы ==========
    
    def __str__(self) -> str:
        return f"User(id={self.id}, email={self.email}, username={self.username})"
    
    def __repr__(self) -> str:
        return (
            f"User(id={self.id}, email='{self.email}', "
            f"username='{self.username}', is_active={self.is_active})"
        )
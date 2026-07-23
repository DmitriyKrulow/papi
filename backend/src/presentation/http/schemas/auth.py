# src/presentation/http/schemas/auth.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, EmailStr


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Имя пользователя")
    email: EmailStr = Field(..., description="Email адрес")
    full_name: Optional[str] = Field(None, max_length=100, description="ФИО")
    phone: Optional[str] = Field(None, description="Телефон")
    department: Optional[str] = Field(None, max_length=255, description="Подразделение")
    role: str = Field("user", max_length=50, description="Роль пользователя")
    is_active: bool = Field(True, description="Активен ли пользователь")


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=255, description="Пароль (обязательное поле)")


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Имя пользователя")
    email: Optional[EmailStr] = Field(None, description="Email адрес")
    full_name: Optional[str] = Field(None, max_length=100, description="ФИО")
    phone: Optional[str] = Field(None, description="Телефон")
    department: Optional[str] = Field(None, max_length=255, description="Подразделение")
    role: Optional[str] = Field(None, max_length=50, description="Роль пользователя")
    is_active: Optional[bool] = Field(None, description="Активен ли пользователь")


class UserResponse(UserBase):
    id: int = Field(..., description="ID пользователя")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: datetime = Field(..., description="Дата последнего обновления")


class UserLogin(BaseModel):
    username: str = Field(..., description="Имя пользователя")
    password: str = Field(..., description="Пароль")


class UserToken(BaseModel):
    access_token: str = Field(..., description="JWT токен доступа")
    token_type: str = Field("bearer", description="Тип токена")


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None


class ProfileUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Имя пользователя")
    email: Optional[EmailStr] = Field(None, description="Email адрес")
    full_name: Optional[str] = Field(None, max_length=100, description="ФИО")
    phone: Optional[str] = Field(None, description="Телефон")


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., description="Старый пароль")
    new_password: str = Field(..., min_length=6, max_length=255, description="Новый пароль")

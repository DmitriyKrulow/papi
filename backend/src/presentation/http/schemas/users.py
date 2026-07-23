# src/presentation/http/schemas/users.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, EmailStr, ConfigDict


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Имя пользователя")
    email: EmailStr = Field(..., description="Email адрес")
    full_name: Optional[str] = Field(None, max_length=100, description="ФИО")
    phone: Optional[str] = Field(None, description="Телефон")
    department: Optional[str] = Field(None, max_length=255, description="Подразделение")
    role: str = Field("user", max_length=50, description="Роль пользователя")
    is_active: bool = Field(True, description="Активен ли пользователь")


class UserCreate(UserBase):
    pass


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

    model_config = ConfigDict(from_attributes=True)

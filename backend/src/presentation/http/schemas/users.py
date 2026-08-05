# src/presentation/http/schemas/users.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, EmailStr, ConfigDict


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Имя пользователя")
    email: EmailStr = Field(..., description="Email")
    full_name: Optional[str] = Field(None, max_length=100, description="ФИО")
    phone: Optional[str] = Field(None, description="Телефон")
    department: Optional[str] = Field(None, max_length=255, description="Подразделение")
    role: str = Field("user", max_length=50, description="Роль пользователя")
    is_active: bool = Field(True, description="Статус активации")
    allowed_ips: Optional[list[str]] = Field(None, description="Whitelist IP адресов (для администраторов)")


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Имя пользователя")
    email: Optional[EmailStr] = Field(None, description="Email")
    full_name: Optional[str] = Field(None, max_length=100, description="ФИО")
    phone: Optional[str] = Field(None, description="Телефон")
    department: Optional[str] = Field(None, max_length=255, description="Подразделение")
    role: Optional[str] = Field(None, max_length=50, description="Роль пользователя")
    is_active: Optional[bool] = Field(None, description="Статус активации")
    allowed_ips: Optional[list[str]] = Field(None, description="Whitelist IP адресов (для администраторов)")


class UserResponse(UserBase):
    id: int = Field(..., description="ID ????????????")
    created_at: datetime = Field(..., description="???? ????????")
    updated_at: datetime = Field(..., description="???? ?????????? ??????????")

    model_config = ConfigDict(from_attributes=True)



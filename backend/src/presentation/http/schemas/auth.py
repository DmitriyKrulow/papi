# src/presentation/http/schemas/auth.py
from datetime import datetime
from typing import Optional
import re

from pydantic import BaseModel, Field, EmailStr, field_validator


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    full_name: Optional[str] = Field(None, max_length=100, description="Full name")
    phone: Optional[str] = Field(None, description="Phone number")
    department: Optional[str] = Field(None, max_length=255, description="Department")
    role: str = Field("user", max_length=50, description="User role")
    is_active: bool = Field(True, description="Is user active")


def _validate_password(value: str) -> str:
    """Validate password strength: min 8 chars, letters + digits."""
    if len(value) < 8:
        raise ValueError("Password must contain at least 8 characters")
    if not re.search(r"[A-Za-z]", value):
        raise ValueError("Password must contain at least one letter")
    if not re.search(r"[0-9]", value):
        raise ValueError("Password must contain at least one digit")
    return value


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=255, description="Password (min 8 characters)")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _validate_password(v)


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Username")
    email: Optional[EmailStr] = Field(None, description="Email address")
    full_name: Optional[str] = Field(None, max_length=100, description="Full name")
    phone: Optional[str] = Field(None, description="Phone number")
    department: Optional[str] = Field(None, max_length=255, description="Department")
    role: Optional[str] = Field(None, max_length=50, description="User role")
    is_active: Optional[bool] = Field(None, description="Is user active")


class UserResponse(UserBase):
    id: int = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Created timestamp")
    updated_at: datetime = Field(..., description="Last updated timestamp")


class UserLogin(BaseModel):
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class UserToken(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None


class ProfileUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Username")
    email: Optional[EmailStr] = Field(None, description="Email address")
    full_name: Optional[str] = Field(None, max_length=100, description="Full name")
    phone: Optional[str] = Field(None, description="Phone number")


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., description="Old password")
    new_password: str = Field(..., min_length=8, max_length=255, description="New password")

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _validate_password(v)

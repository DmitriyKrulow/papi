# src/presentation/http/schemas/assets.py
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class AssetBase(BaseModel):
    inventory_number: str = Field(..., min_length=1, max_length=100, description="Инвентарный номер")
    name: str = Field(..., min_length=1, max_length=255, description="Название актива")
    description: Optional[str] = Field(None, max_length=1000, description="Описание")
    model: str = Field("", max_length=255, description="Модель")
    manufacturer_code: Optional[str] = Field(None, max_length=100, description="Код производителя")
    manufacturer_name: Optional[str] = Field(None, max_length=255, description="Название производителя")
    purchase_price: Optional[str] = Field(None, description="Стоимость покупки (рубли)")
    current_value: Optional[str] = Field(None, description="Текущая стоимость (рубли)")
    status: str = Field("active", description="Статус актива")
    location_address: Optional[str] = Field(None, max_length=500, description="Адрес местоположения")
    responsible_person: Optional[str] = Field(None, max_length=255, description="Ответственное лицо")
    purchase_date: Optional[date] = Field(None, description="Дата покупки")
    commissioning_date: Optional[date] = Field(None, description="Дата ввода в эксплуатацию")
    warranty_expiry: Optional[date] = Field(None, description="Окончание гарантии")


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Название актива")
    description: Optional[str] = Field(None, max_length=1000, description="Описание")
    model: Optional[str] = Field(None, max_length=255, description="Модель")
    manufacturer_code: Optional[str] = Field(None, max_length=100, description="Код производителя")
    manufacturer_name: Optional[str] = Field(None, max_length=255, description="Название производителя")
    purchase_price: Optional[str] = Field(None, description="Стоимость покупки (рубли)")
    current_value: Optional[str] = Field(None, description="Текущая стоимость (рубли)")
    status: Optional[str] = Field(None, description="Статус актива")
    location_address: Optional[str] = Field(None, max_length=500, description="Адрес местоположения")
    responsible_person: Optional[str] = Field(None, max_length=255, description="Ответственное лицо")
    purchase_date: Optional[date] = Field(None, description="Дата покупки")
    commissioning_date: Optional[date] = Field(None, description="Дата ввода в эксплуатацию")
    warranty_expiry: Optional[date] = Field(None, description="Окончание гарантии")


class AssetResponse(AssetBase):
    id: int = Field(..., description="ID актива")
    is_active: bool = Field(..., description="Активен ли актив")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: datetime = Field(..., description="Дата последнего обновления")

    model_config = ConfigDict(from_attributes=True)

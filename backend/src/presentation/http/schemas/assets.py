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
    purchase_price: Optional[str] = Field(None, description="Приобретательная цена (рубли)")
    current_value: Optional[str] = Field(None, description="Текущая стоимость (рубли)")
    status: str = Field("active", description="Статус актива")
    location_address: Optional[str] = Field(None, max_length=500, description="Место местонахождения")
    responsible_person: Optional[str] = Field(None, max_length=255, description="Ответственное лицо")
    purchase_date: Optional[date] = Field(None, description="Дата покупки")
    commissioning_date: Optional[date] = Field(None, description="Дата ввода в эксплуатацию")
    warranty_expiry: Optional[date] = Field(None, description="Окончание гарантии")
    rfid_tag: Optional[str] = Field(None, max_length=100, description="RFID-метка актива")


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Название актива")
    description: Optional[str] = Field(None, max_length=1000, description="Описание")
    model: Optional[str] = Field(None, max_length=255, description="Модель")
    manufacturer_code: Optional[str] = Field(None, max_length=100, description="Код производителя")
    manufacturer_name: Optional[str] = Field(None, max_length=255, description="Название производителя")
    purchase_price: Optional[str] = Field(None, description="Приобретательная цена (рубли)")
    current_value: Optional[str] = Field(None, description="Текущая стоимость (рубли)")
    status: Optional[str] = Field(None, description="Статус актива")
    location_address: Optional[str] = Field(None, max_length=500, description="Место местонахождения")
    responsible_person: Optional[str] = Field(None, max_length=255, description="Ответственное лицо")
    purchase_date: Optional[date] = Field(None, description="Дата покупки")
    commissioning_date: Optional[date] = Field(None, description="Дата ввода в эксплуатацию")
    warranty_expiry: Optional[date] = Field(None, description="Окончание гарантии")
    rfid_tag: Optional[str] = Field(None, max_length=100, description="RFID-метка актива")


class AssetResponse(AssetBase):
    id: int = Field(..., description="ID актива")
    is_active: bool = Field(..., description="Активен ли актив")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: datetime = Field(..., description="Дата последнего изменения")
    # Поля инвентаризации
    last_inventory_date: Optional[datetime] = Field(None, description="Дата последней проверки")
    last_inventory_by_id: Optional[int] = Field(None, description="ID проверяющего, подтвердившего проверку")
    last_inventory_confirmed: Optional[bool] = Field(None, description="Подтверждён ли актив")
    last_inventory_source: Optional[str] = Field(None, description="Источник проверки: 'manual' | 'rfid'")
    rfid_tag: Optional[str] = Field(None, description="RFID-метка актива")

    model_config = ConfigDict(from_attributes=True)



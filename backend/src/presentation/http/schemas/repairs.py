# src/presentation/http/schemas/repairs.py
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class RepairBase(BaseModel):
    asset_id: int = Field(..., gt=0, description="ID актива")
    repair_date: date = Field(..., description="Дата ремонта")
    repair_type: str = Field(..., max_length=100, description="Тип ремонта")
    description: str = Field(..., max_length=1000, description="Описание ремонта")
    cost: Optional[Decimal] = Field(None, gt=0, description="Стоимость ремонта")
    performer: Optional[str] = Field(None, max_length=255, description="Исполнитель")
    status: str = Field("draft", max_length=50, description="Статус ремонта")


class RepairCreate(RepairBase):
    pass


class RepairUpdate(BaseModel):
    asset_id: Optional[int] = Field(None, gt=0, description="ID актива")
    repair_date: Optional[date] = Field(None, description="Дата ремонта")
    repair_type: Optional[str] = Field(None, max_length=100, description="Тип ремонта")
    description: Optional[str] = Field(None, max_length=1000, description="Описание ремонта")
    cost: Optional[Decimal] = Field(None, gt=0, description="Стоимость ремонта")
    performer: Optional[str] = Field(None, max_length=255, description="Исполнитель")
    status: Optional[str] = Field(None, max_length=50, description="Статус ремонта")
    started_at: Optional[datetime] = Field(None, description="Начало ремонта")
    completed_at: Optional[datetime] = Field(None, description="Окончание ремонта")


class RepairResponse(RepairBase):
    id: int = Field(..., description="ID ремонта")
    asset_id: int = Field(..., description="ID актива")
    repair_date: date = Field(..., description="Дата ремонта")
    repair_type: str = Field(..., description="Тип ремонта")
    description: str = Field(..., description="Описание ремонта")
    cost: Optional[Decimal] = Field(None, description="Стоимость ремонта")
    performer: Optional[str] = Field(None, description="Исполнитель")
    status: str = Field("draft", description="Статус ремонта")
    started_at: Optional[datetime] = Field(None, description="Начало ремонта")
    completed_at: Optional[datetime] = Field(None, description="Окончание ремонта")
    created_at: datetime = Field(..., description="Дата создания")

    model_config = ConfigDict(from_attributes=True)

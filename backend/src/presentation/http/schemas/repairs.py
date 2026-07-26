# src/presentation/http/schemas/repairs.py
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class RepairRequestBase(BaseModel):
    asset_id: int = Field(..., gt=0, description="ID актива")
    title: str = Field(..., max_length=255, description="Название заявки")
    description: str = Field(..., max_length=1000, description="Описание заявки")
    priority: str = Field("medium", description="Приоритет заявки")
    desired_completion_date: Optional[date] = Field(None, description="Желаемая дата завершения")
    deadline: Optional[date] = Field(None, description="Срок выполнения")
    estimated_cost: Optional[Decimal] = Field(None, ge=0, description="Ориентировочная стоимость")


class RepairRequestCreate(RepairRequestBase):
    pass


class RepairRequestUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255, description="Название заявки")
    description: Optional[str] = Field(None, max_length=1000, description="Описание заявки")
    priority: Optional[str] = Field(None, description="Приоритет заявки")
    desired_completion_date: Optional[date] = Field(None, description="Желаемая дата завершения")
    deadline: Optional[date] = Field(None, description="Срок выполнения")
    estimated_cost: Optional[Decimal] = Field(None, ge=0, description="Ориентировочная стоимость")


class RepairStatusUpdate(BaseModel):
    status: str
    assigned_to: Optional[int] = None
    actual_completion_date: Optional[date] = None
    actual_cost: Optional[Decimal] = None
    completion_notes: Optional[str] = None
    rejection_reason: Optional[str] = None


class RepairPriorityUpdate(BaseModel):
    priority: str = Field(..., description="Новый приоритет заявки")


class RepairTemplateBase(BaseModel):
    name: str = Field(..., max_length=255, description="Название шаблона")
    description: Optional[str] = Field(None, max_length=1000, description="Описание шаблона")
    template_data: Optional[dict] = Field(default_factory=dict, description="Данные шаблона")
    is_default: bool = Field(False, description="Шаблон по умолчанию")


class RepairTemplateCreate(RepairTemplateBase):
    pass


class RepairTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255, description="Название шаблона")
    description: Optional[str] = Field(None, max_length=1000, description="Описание шаблона")
    template_data: Optional[dict] = Field(default_factory=dict, description="Данные шаблона")
    is_default: Optional[bool] = Field(None, description="Шаблон по умолчанию")


class RepairTemplateApply(BaseModel):
    asset_id: int = Field(..., gt=0, description="ID актива для применения шаблона")


class RepairRequestResponse(RepairRequestBase):
    id: int = Field(..., description="ID заявки")
    status: str = Field(..., description="Статус заявки")
    created_by: int = Field(..., description="ID создателя")
    creator_name: Optional[str] = Field(None, description="Имя создателя")
    created_at: datetime = Field(..., description="Дата создания")
    assigned_to: Optional[int] = Field(None, description="ID исполнителя")
    assigned_at: Optional[datetime] = Field(None, description="Дата назначения")
    actual_completion_date: Optional[date] = Field(None, description="Фактическая дата завершения")
    actual_cost: Optional[Decimal] = Field(None, description="Фактическая стоимость")
    completion_notes: Optional[str] = Field(None, description="Примечания о завершении")
    rejection_reason: Optional[str] = Field(None, description="Причина отклонения")
    updated_at: datetime = Field(..., description="Дата обновления")
    asset_name: Optional[str] = Field(None, description="Название актива")
    inventory_number: Optional[str] = Field(None, description="Инвентарный номер")
    assigned_to_name: Optional[str] = Field(None, description="Имя исполнителя")

    model_config = ConfigDict(from_attributes=True)


class RepairTemplateResponse(RepairTemplateBase):
    id: int = Field(..., description="ID шаблона")
    is_active: bool = Field(..., description="Активен ли шаблон")
    created_by: int = Field(..., description="ID создателя")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: datetime = Field(..., description="Дата обновления")

    model_config = ConfigDict(from_attributes=True)


class RepairRequestListResponse(BaseModel):
    items: list[RepairRequestResponse]
    total: int
    skip: int
    limit: int


class RepairTemplateListResponse(BaseModel):
    items: list[RepairTemplateResponse]
    total: int
    skip: int
    limit: int

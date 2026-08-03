# src/core/entities/asset_photo.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class PhotoStage(Enum):
    """Этап жизненного цикла актива, на котором сделано фото"""
    RECEIVING = "receiving"
    INVENTORY = "inventory"
    WRITE_OFF = "write_off"
    REPAIR = "repair"
    MAINTENANCE = "maintenance"
    MOVEMENT = "movement"
    OTHER = "other"


class PhotoCategory(Enum):
    """Категория фотографии внутри этапа"""
    GENERAL_VIEW = "general_view"
    PLACEMENT = "placement"
    INVENTORY_NUMBER = "inventory_number"
    CURRENT_LOCATION = "current_location"
    CONDITION = "condition"
    MALFUNCTION = "malfunction"
    GENERAL_CONDITION = "general_condition"


@dataclass
class AssetPhoto:
    """
    Сущность "Фотография актива".
    """
    id: int
    asset_id: int
    document_id: int
    uploaded_by: int
    
    # Этап на жизненном цикле актива
    stage: PhotoStage = PhotoStage.OTHER
    # Категория фото внутри этапа
    photo_category: Optional[str] = None
    
    description: Optional[str] = None
    taken_at: Optional[datetime] = None
    taken_by: Optional[int] = None
    uploaded_at: datetime = field(default_factory=datetime.now)
    
    inventory_check_id: Optional[int] = None
    repair_request_id: Optional[int] = None
    
    is_before: bool = False
    is_after: bool = False
    sort_order: int = 0
    
    def get_stage_display(self) -> str:
        """Возвращает читаемое название этапа"""
        stages = {
            PhotoStage.RECEIVING: "При поступлении",
            PhotoStage.INVENTORY: "При инвентаризации",
            PhotoStage.WRITE_OFF: "Перед списанием",
            PhotoStage.REPAIR: "Во время ремонта",
            PhotoStage.MAINTENANCE: "Во время ТО",
            PhotoStage.MOVEMENT: "При перемещении",
            PhotoStage.OTHER: "Другое",
        }
        return stages.get(self.stage, str(self.stage))
    
    def get_category_display(self) -> str:
        """Возвращает читаемое название категории"""
        categories = {
            PhotoCategory.GENERAL_VIEW: "Общий вид",
            PhotoCategory.PLACEMENT: "Место размещения",
            PhotoCategory.INVENTORY_NUMBER: "Инвентарный номер",
            PhotoCategory.CURRENT_LOCATION: "Текущее место расположения",
            PhotoCategory.CONDITION: "Состояние",
            PhotoCategory.MALFUNCTION: "Неисправность",
            PhotoCategory.GENERAL_CONDITION: "Общее состояние",
        }
        if self.photo_category:
            try:
                cat = PhotoCategory(self.photo_category)
                return categories.get(cat, self.photo_category)
            except ValueError:
                return self.photo_category
        return ""
    
    def __str__(self) -> str:
        return f"AssetPhoto(id={self.id}, asset_id={self.asset_id}, stage={self.stage})"


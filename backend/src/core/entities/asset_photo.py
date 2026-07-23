# src/core/entities/asset_photo.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class PhotoStage(Enum):
    """Этап жизненного цикла, на котором сделано фото"""
    RECEIVING = "receiving"
    INVENTORY = "inventory"
    WRITE_OFF = "write_off"
    REPAIR = "repair"
    MAINTENANCE = "maintenance"
    MOVEMENT = "movement"
    OTHER = "other"


@dataclass
class AssetPhoto:
    """
    Сущность "Фотография актива".
    """
    id: int
    asset_id: int
    document_id: int
    uploaded_by: int
    
    # Поля со значениями по умолчанию
    stage: PhotoStage = PhotoStage.OTHER
    
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
        """Читаемое название этапа"""
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
    
    def __str__(self) -> str:
        return f"AssetPhoto(id={self.id}, asset_id={self.asset_id}, stage={self.stage})"
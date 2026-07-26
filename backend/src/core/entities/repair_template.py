from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

from src.core.value_objects import Money


@dataclass
class RepairTemplate:
    """Сущность шаблона заявки на ремонт"""
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    template_data: Dict[str, Any] = field(default_factory=dict)
    
    is_active: bool = True
    is_default: bool = False
    
    created_by: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    creator_name: Optional[str] = None
    
    def activate(self) -> None:
        """Активировать шаблон"""
        self.is_active = True
    
    def deactivate(self) -> None:
        """Деактивировать шаблон"""
        self.is_active = False
    
    def set_as_default(self) -> None:
        """Установить как шаблон по умолчанию"""
        self.is_default = True
    
    def apply_to_repair_request(self, asset_name: str) -> Dict[str, Any]:
        """Применить шаблон к заявке и вернуть данные для создания заявки"""
        base_data = {
            "title": f"{self.name} - {asset_name}",
            "description": self.template_data.get("description", self.description),
            "priority": self.template_data.get("priority", "medium"),
            "desired_completion_date": self.template_data.get("desired_completion_date"),
            "deadline": self.template_data.get("deadline"),
            "estimated_cost": self.template_data.get("estimated_cost"),
        }
        
        return {k: v for k, v in base_data.items() if v is not None}

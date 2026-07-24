# src/core/entities/report.py
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from enum import Enum


class ReportType(Enum):
    """???? ???????"""
    ASSET_LIST = "asset_list"
    ASSET_CARD = "asset_card"
    DEPRECIATION = "depreciation"
    MOVEMENT = "movement"
    MAINTENANCE = "maintenance"
    REPAIR = "repair"
    INVENTORY = "inventory"
    WRITE_OFF = "write_off"
    SUMMARY = "summary"
    TAX = "tax"
    CUSTOM = "custom"


class ReportFormat(Enum):
    """??????? ???????"""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    HTML = "html"
    JSON = "json"


class ReportStatus(Enum):
    """?????? ??????"""
    GENERATING = "generating"
    READY = "ready"
    ERROR = "error"
    DELETED = "deleted"


@dataclass
class Report:
    """
    ???????? "?????".
    """
    id: int
    name: str
    report_type: ReportType
    format: ReportFormat
    created_by: int
    
    # ???? ?? ?????????? ?? ?????????
    parameters: Dict[str, Any] = field(default_factory=dict)
    filters: Dict[str, Any] = field(default_factory=dict)
    
    status: ReportStatus = ReportStatus.GENERATING
    error_message: Optional[str] = None
    
    document_id: Optional[int] = None
    
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    
    created_at: datetime = field(default_factory=datetime.now)
    generated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    def mark_ready(self, document_id: int) -> None:
        """???????? ????? ??? ???????"""
        self.status = ReportStatus.READY
        self.document_id = document_id
        self.generated_at = datetime.now()
    
    def mark_error(self, error_message: str) -> None:
        """???????? ????? ??? ?????????"""
        self.status = ReportStatus.ERROR
        self.error_message = error_message
    
    def is_ready(self) -> bool:
        """????? ?? ????? ? ??????????"""
        return self.status == ReportStatus.READY
    
    def is_expired(self) -> bool:
        """????????? ?? ?????"""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at
    
    def get_type_display(self) -> str:
        """???????? ???????? ???? ??????"""
        types = {
            ReportType.ASSET_LIST: "?????? ???????",
            ReportType.ASSET_CARD: "???????? ??????",
            ReportType.DEPRECIATION: "???????????",
            ReportType.MOVEMENT: "???????????",
            ReportType.MAINTENANCE: "??????????? ????????????",
            ReportType.REPAIR: "???????",
            ReportType.INVENTORY: "??????????????",
            ReportType.WRITE_OFF: "????????",
            ReportType.SUMMARY: "??????",
            ReportType.TAX: "????????? ????",
            ReportType.CUSTOM: "????????????????",
        }
        return types.get(self.report_type, str(self.report_type))
    
    def get_format_display(self) -> str:
        """???????? ???????? ???????"""
        formats = {
            ReportFormat.PDF: "PDF",
            ReportFormat.EXCEL: "Excel",
            ReportFormat.CSV: "CSV",
            ReportFormat.HTML: "HTML",
            ReportFormat.JSON: "JSON",
        }
        return formats.get(self.format, str(self.format))
    
    def __str__(self) -> str:
        return f"Report(id={self.id}, name='{self.name}', type={self.report_type})"


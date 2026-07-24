# src/core/entities/import_job.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class ImportStatus(Enum):
    """?????? ???????"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class ImportType(Enum):
    """??? ???????"""
    ASSETS = "assets"
    EMPLOYEES = "employees"
    DEPARTMENTS = "departments"
    SUPPLIERS = "suppliers"
    CONTRACTS = "contracts"
    INVENTORY = "inventory"


@dataclass
class ImportJob:
    """
    ???????? "?????? ???????".
    """
    id: int
    filename: str
    import_type: ImportType
    created_by: int
    
    # ???? ?? ?????????? ?? ?????????
    status: ImportStatus = ImportStatus.PENDING
    total_rows: int = 0
    processed_rows: int = 0
    successful_rows: int = 0
    failed_rows: int = 0
    
    errors: List[Dict[str, Any]] = field(default_factory=list)
    error_file_id: Optional[int] = None
    result_file_id: Optional[int] = None
    summary: Dict[str, Any] = field(default_factory=dict)
    
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def start(self) -> None:
        """?????? ??????"""
        if self.status != ImportStatus.PENDING:
            raise ValueError(f"Cannot start import with status {self.status}")
        self.status = ImportStatus.PROCESSING
        self.started_at = datetime.now()
    
    def complete(self, successful: int, failed: int, errors: List[Dict[str, Any]]) -> None:
        """????????? ??????"""
        if self.status != ImportStatus.PROCESSING:
            raise ValueError(f"Cannot complete import with status {self.status}")
        
        self.processed_rows = successful + failed
        self.successful_rows = successful
        self.failed_rows = failed
        self.errors = errors
        self.completed_at = datetime.now()
        
        if failed > 0 and successful > 0:
            self.status = ImportStatus.PARTIAL
        elif failed > 0:
            self.status = ImportStatus.FAILED
        else:
            self.status = ImportStatus.COMPLETED
    
    def fail(self, error_message: str) -> None:
        """???????? ?????? ??? ?????????"""
        self.status = ImportStatus.FAILED
        self.errors = [{'message': error_message, 'timestamp': datetime.now().isoformat()}]
        self.completed_at = datetime.now()
    
    def get_progress(self) -> float:
        """??????? ??????????"""
        if self.total_rows == 0:
            return 0.0
        return (self.processed_rows / self.total_rows) * 100
    
    def get_status_display(self) -> str:
        """???????? ???????? ???????"""
        statuses = {
            ImportStatus.PENDING: "???????",
            ImportStatus.PROCESSING: "? ????????",
            ImportStatus.COMPLETED: "????????",
            ImportStatus.PARTIAL: "???????? ????????",
            ImportStatus.FAILED: "?? ??????",
        }
        return statuses.get(self.status, str(self.status))
    
    def get_type_display(self) -> str:
        """???????? ???????? ????"""
        types = {
            ImportType.ASSETS: "??????",
            ImportType.EMPLOYEES: "??????????",
            ImportType.DEPARTMENTS: "?????????????",
            ImportType.SUPPLIERS: "??????????",
            ImportType.CONTRACTS: "????????",
            ImportType.INVENTORY: "??????????????",
        }
        return types.get(self.import_type, str(self.import_type))
    
    def __str__(self) -> str:
        return f"ImportJob(id={self.id}, filename='{self.filename}', type={self.import_type})"


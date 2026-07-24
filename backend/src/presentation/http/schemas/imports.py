from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ImportValidationResult:
    """????????? ????????? ????? ?????? ??? ???????"""
    row_number: int
    inventory_number: str
    name: str
    quantity: int
    value: float
    is_valid: bool
    action: str
    errors: Optional[str] = None
    existing_asset_id: Optional[int] = None


@dataclass
class ImportReportResponse:
    """????? ? ??????? ?? ???????"""
    total_rows: int
    successful: int
    validation_errors: int
    create_count: int
    update_count: int
    validation_results: List[ImportValidationResult]



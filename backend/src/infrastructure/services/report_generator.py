# src/infrastructure/services/report_generator.py
import os
import json
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from decimal import Decimal

from sqlalchemy.orm import Session

# Правильный импорт модели Asset
from src.infrastructure.db.models.asset import Asset
from src.infrastructure.db.models.depreciation_record import DepreciationRecord


class ReportGenerator:
    """Сервис для генерации отчетов"""
    
    REPORT_DIR = "uploads/reports"
    
    def __init__(self, db: Session):
        self.db = db
        os.makedirs(self.REPORT_DIR, exist_ok=True)
    
    def generate(
        self,
        report_id: int,
        report_type: str,
        format: str,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Генерирует отчет указанного типа.
        """
        if report_type == "assets":
            return self._generate_assets_report(report_id, format, period_start, period_end, filters)
        elif report_type == "depreciation":
            return self._generate_depreciation_report(report_id, format, period_start, period_end, filters)
        elif report_type == "inventory":
            return self._generate_inventory_report(report_id, format, period_start, period_end, filters)
        else:
            raise ValueError(f"Unknown report type: {report_type}")
    
    def _generate_assets_report(self, report_id: int, format: str, period_start, period_end, filters) -> str:
        """Генерирует отчет по активам"""
        # Получаем данные
        query = self.db.query(Asset)
        
        if period_start:
            query = query.filter(Asset.created_at >= period_start)
        if period_end:
            query = query.filter(Asset.created_at <= period_end)
        
        assets = query.all()
        
        # Формируем данные
        data = {
            'title': 'Отчет по активам',
            'generated_at': datetime.now().isoformat(),
            'period': {
                'start': period_start.isoformat() if period_start else None,
                'end': period_end.isoformat() if period_end else None,
            },
            'total_assets': len(assets),
            'total_value': sum(float(a.current_value) if a.current_value else 0 for a in assets),
            'assets': [
                {
                    'id': a.id,
                    'inventory_number': str(a.inventory_number),
                    'name': a.name,
                    'current_value': float(a.current_value) if a.current_value else 0,
                    'status': a.status,
                }
                for a in assets
            ]
        }
        
        # Сохраняем в зависимости от формата
        file_path = os.path.join(self.REPORT_DIR, f"report_{report_id}.{format}")
        
        if format == 'json':
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        else:
            # Для других форматов используем простую текстовую заглушку
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"Report {report_id}\n")
                f.write(f"Type: assets\n")
                f.write(f"Format: {format}\n")
                f.write(f"Generated: {datetime.now()}\n")
                f.write(f"Total assets: {len(assets)}\n")
        
        return file_path
    
    def _generate_depreciation_report(self, report_id: int, format: str, period_start, period_end, filters) -> str:
        """Генерирует отчет по амортизации"""
        file_path = os.path.join(self.REPORT_DIR, f"report_{report_id}.{format}")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"Depreciation Report {report_id}\n")
            f.write(f"Generated: {datetime.now()}\n")
        
        return file_path
    
    def _generate_inventory_report(self, report_id: int, format: str, period_start, period_end, filters) -> str:
        """Генерирует инвентаризационный отчет"""
        file_path = os.path.join(self.REPORT_DIR, f"report_{report_id}.{format}")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"Inventory Report {report_id}\n")
            f.write(f"Generated: {datetime.now()}\n")
        
        return file_path
    
    @staticmethod
    def get_mime_type(format: str) -> str:
        """Возвращает mime-type для формата"""
        mime_types = {
            'pdf': 'application/pdf',
            'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'csv': 'text/csv',
            'html': 'text/html',
            'json': 'application/json',
        }
        return mime_types.get(format, 'application/octet-stream')
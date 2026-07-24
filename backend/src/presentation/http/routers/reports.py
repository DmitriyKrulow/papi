# backend/src/presentation/http/routers/reports.py
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Any
import os
import json  # Добавляем импорт json

# Добавляем импорты для Excel
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

from src.infrastructure.db.init_db import get_db
from src.infrastructure.services.report_exporter import ReportExporter

# Путь для сохранения отчетов
REPORTS_DIR = "uploads/reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

router = APIRouter(prefix="/reports", tags=["reports"])


def safe_decimal_to_float(value: Optional[Any], default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        if isinstance(value, (int, float)):
            return float(value)
        return default
    except (TypeError, ValueError):
        return default


def safe_str(value: Optional[Any], default: str = "") -> str:
    if value is None:
        return default
    try:
        return str(value)
    except (TypeError, ValueError):
        return default


def safe_isoformat(value: Optional[Any]) -> Optional[str]:
    if value is None:
        return None
    try:
        if hasattr(value, 'isoformat') and callable(getattr(value, 'isoformat')):
            return value.isoformat()
        return str(value)
    except (AttributeError, ValueError):
        return None


def get_worksheet(wb: Workbook):
    """Безопасно получает активный лист"""
    ws = wb.active
    if ws is None:
        ws = wb.create_sheet("Sheet1")
    return ws


# ==================== Отчет по активам ====================

@router.get("/asset-report")
async def get_asset_report(db: Session = Depends(get_db)):
    """Отчет по активам (JSON)"""
    try:
        from src.infrastructure.db.models.asset import Asset
        assets = db.query(Asset).limit(100).all()
        
        assets_list = []
        for asset in assets:
            assets_list.append({
                "id": getattr(asset, 'id', None),
                "inventory_number": safe_str(getattr(asset, 'inventory_number', None)),
                "name": safe_str(getattr(asset, 'name', None)),
                "description": safe_str(getattr(asset, 'description', None)),
                "model": safe_str(getattr(asset, 'model', None)),
                "asset_type": safe_str(getattr(asset, 'asset_type', None)),
                "status": safe_str(getattr(asset, 'status', None)),
                "current_value": safe_decimal_to_float(getattr(asset, 'current_value', None)),
                "purchase_price": safe_decimal_to_float(getattr(asset, 'purchase_price', None)),
                "department_code": safe_str(getattr(asset, 'department_code', None)),
                "responsible_person": safe_str(getattr(asset, 'responsible_person', None)),
                "created_at": safe_isoformat(getattr(asset, 'created_at', None)),
                "updated_at": safe_isoformat(getattr(asset, 'updated_at', None)),
            })
        
        return JSONResponse(content={
            "title": "Отчет по активам",
            "generated_at": datetime.now().isoformat(),
            "total_assets": len(assets_list),
            "assets": assets_list
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


@router.get("/asset-report/export")
async def export_asset_report(
    format: str = Query("excel", description="Формат: excel, pdf, json"),
    db: Session = Depends(get_db),
):
    """Экспорт отчета по активам в выбранном формате"""
    try:
        from src.infrastructure.db.models.asset import Asset
        assets = db.query(Asset).limit(100).all()
        
        assets_list = []
        for asset in assets:
            assets_list.append({
                "id": getattr(asset, 'id', None),
                "inventory_number": safe_str(getattr(asset, 'inventory_number', None)),
                "name": safe_str(getattr(asset, 'name', None)),
                "description": safe_str(getattr(asset, 'description', None)),
                "model": safe_str(getattr(asset, 'model', None)),
                "asset_type": safe_str(getattr(asset, 'asset_type', None)),
                "status": safe_str(getattr(asset, 'status', None)),
                "current_value": safe_decimal_to_float(getattr(asset, 'current_value', None)),
                "purchase_price": safe_decimal_to_float(getattr(asset, 'purchase_price', None)),
                "department_code": safe_str(getattr(asset, 'department_code', None)),
                "responsible_person": safe_str(getattr(asset, 'responsible_person', None)),
                "created_at": safe_isoformat(getattr(asset, 'created_at', None)),
                "updated_at": safe_isoformat(getattr(asset, 'updated_at', None)),
            })
        
        data = {
            "title": "Отчет по активам",
            "generated_at": datetime.now().isoformat(),
            "total_assets": len(assets_list),
            "assets": assets_list
        }
        
        filepath = ReportExporter.export_asset_report(data, format)
        filename = os.path.basename(filepath)
        
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type="application/octet-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка экспорта: {str(e)}")


# ==================== Отчет по амортизации ====================

@router.get("/depreciation-report")
async def get_depreciation_report(db: Session = Depends(get_db)):
    """Отчет по амортизации (JSON)"""
    try:
        from src.infrastructure.db.models.depreciation_record import DepreciationRecord
        records = db.query(DepreciationRecord).limit(100).all()
        
        records_list = []
        for record in records:
            period_start = getattr(record, 'period_start', None)
            period_end = getattr(record, 'period_end', None)
            period_str = ""
            if period_start and period_end:
                period_str = f"{period_start} - {period_end}"
            
            records_list.append({
                "id": getattr(record, 'id', None),
                "asset_id": getattr(record, 'asset_id', None),
                "period_start": safe_isoformat(period_start),
                "period_end": safe_isoformat(period_end),
                "period": period_str,
                "amount": safe_decimal_to_float(getattr(record, 'depreciation_amount', None)),
                "accumulated": safe_decimal_to_float(getattr(record, 'accumulated_depreciation', None)),
                "book_value_before": safe_decimal_to_float(getattr(record, 'book_value_before', None)),
                "book_value_after": safe_decimal_to_float(getattr(record, 'book_value_after', None)),
                "rate": safe_decimal_to_float(getattr(record, 'rate', None)),
                "method": safe_str(getattr(record, 'method', None)),
                "created_at": safe_isoformat(getattr(record, 'created_at', None)),
            })
        
        return JSONResponse(content={
            "title": "Отчет по амортизации",
            "generated_at": datetime.now().isoformat(),
            "total_records": len(records_list),
            "records": records_list
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


@router.get("/depreciation-report/export")
async def export_depreciation_report(
    format: str = Query("excel", description="Формат: excel, pdf, json"),
    db: Session = Depends(get_db),
):
    """Экспорт отчета по амортизации в выбранном формате"""
    try:
        from src.infrastructure.db.models.depreciation_record import DepreciationRecord
        records = db.query(DepreciationRecord).limit(100).all()
        
        records_list = []
        for record in records:
            period_start = getattr(record, 'period_start', None)
            period_end = getattr(record, 'period_end', None)
            period_str = ""
            if period_start and period_end:
                period_str = f"{period_start} - {period_end}"
            
            records_list.append({
                "id": getattr(record, 'id', None),
                "asset_id": getattr(record, 'asset_id', None),
                "period_start": safe_isoformat(period_start),
                "period_end": safe_isoformat(period_end),
                "period": period_str,
                "amount": safe_decimal_to_float(getattr(record, 'depreciation_amount', None)),
                "accumulated": safe_decimal_to_float(getattr(record, 'accumulated_depreciation', None)),
                "book_value_before": safe_decimal_to_float(getattr(record, 'book_value_before', None)),
                "book_value_after": safe_decimal_to_float(getattr(record, 'book_value_after', None)),
                "rate": safe_decimal_to_float(getattr(record, 'rate', None)),
                "method": safe_str(getattr(record, 'method', None)),
                "created_at": safe_isoformat(getattr(record, 'created_at', None)),
            })
        
        data = {
            "title": "Отчет по амортизации",
            "generated_at": datetime.now().isoformat(),
            "total_records": len(records_list),
            "records": records_list
        }
        
        filepath = ReportExporter.export_depreciation_report(data, format)
        filename = os.path.basename(filepath)
        
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type="application/octet-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка экспорта: {str(e)}")


# ==================== Инвентаризационный отчет ====================

@router.get("/inventory-report")
async def get_inventory_report(db: Session = Depends(get_db)):
    """Инвентаризационный отчет (JSON)"""
    try:
        from src.infrastructure.db.models.asset import Asset
        
        total_assets = db.query(Asset).count()
        active_assets = db.query(Asset).filter(Asset.status == "active").count()
        maintenance_assets = db.query(Asset).filter(Asset.status == "maintenance").count()
        written_off_assets = db.query(Asset).filter(Asset.status == "written_off").count()
        
        return JSONResponse(content={
            "title": "Инвентаризационный отчет",
            "generated_at": datetime.now().isoformat(),
            "stats": {
                "total": total_assets,
                "active": active_assets,
                "maintenance": maintenance_assets,
                "written_off": written_off_assets,
            },
            "message": "Отчет сгенерирован успешно"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inventory-report/export")
async def export_inventory_report(
    format: str = Query("excel", description="Формат: excel, pdf, json"),
    db: Session = Depends(get_db),
):
    """Экспорт инвентаризационного отчета в выбранном формате"""
    try:
        from src.infrastructure.db.models.asset import Asset
        
        total_assets = db.query(Asset).count()
        active_assets = db.query(Asset).filter(Asset.status == "active").count()
        maintenance_assets = db.query(Asset).filter(Asset.status == "maintenance").count()
        written_off_assets = db.query(Asset).filter(Asset.status == "written_off").count()
        
        data = {
            "title": "Инвентаризационный отчет",
            "generated_at": datetime.now().isoformat(),
            "stats": {
                "total": total_assets,
                "active": active_assets,
                "maintenance": maintenance_assets,
                "written_off": written_off_assets,
            },
            "message": "Отчет сгенерирован успешно"
        }
        
        filepath = ReportExporter.export_inventory_report(data, format)
        filename = os.path.basename(filepath)
        
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type="application/octet-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка экспорта: {str(e)}")


# ==================== Отчет по импорту ====================

@router.get("/import-report")
async def get_import_report(db: Session = Depends(get_db)):
    """Отчет по импорту (JSON)"""
    return JSONResponse(content={
        "title": "Отчет по импорту",
        "generated_at": datetime.now().isoformat(),
        "status": "ok",
        "message": "Отчет в разработке"
    })


@router.get("/import-report/export")
async def export_import_report(
    format: str = Query("excel", description="Формат: excel, pdf, json"),
    db: Session = Depends(get_db),
):
    """Экспорт отчета по импорту в выбранном формате"""
    try:
        data = {
            "title": "Отчет по импорту",
            "generated_at": datetime.now().isoformat(),
            "status": "ok",
            "message": "Отчет в разработке",
            "imports": []
        }
        
        if format == "excel":
            # Создаем Excel файл
            wb = Workbook()
            ws = get_worksheet(wb)
            ws.title = "Импорт"
            
            # Заголовок
            ws.merge_cells('A1:B1')
            ws['A1'] = data['title']
            ws['A1'].font = Font(bold=True, size=16)
            ws['A1'].alignment = Alignment(horizontal="center")
            
            ws['A2'] = f"Дата: {data['generated_at']}"
            
            ws['A4'] = "Статус"
            ws['A4'].font = Font(bold=True)
            ws['B4'] = data['status']
            
            ws['A5'] = "Сообщение"
            ws['A5'].font = Font(bold=True)
            ws['B5'] = data['message']
            
            filename = f"import_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            filepath = os.path.join(REPORTS_DIR, filename)
            wb.save(filepath)
        else:
            # JSON формат
            filename = f"import_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(REPORTS_DIR, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type="application/octet-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка экспорта: {str(e)}")


@router.get("/health")
async def reports_health():
    """Проверка доступности сервиса отчетов"""
    return JSONResponse(content={
        "status": "ok",
        "service": "reports",
        "timestamp": datetime.now().isoformat()
    })
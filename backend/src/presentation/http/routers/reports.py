# src/presentation/http/routers/reports.py
from fastapi import APIRouter, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from typing import Optional
from datetime import datetime

router = APIRouter()


@router.get("/asset-report")
async def get_asset_report(
    include_photos: bool = Query(False, description="Включить фотографии"),
    include_history: bool = Query(False, description="Включить историю изменений"),
):
    """Отчет по активам - получить данные"""
    try:
        from backend.src.infrastructure.reports import AssetReportGenerator
        
        assets = [
            {
                'id': 1,
                'inventory_number': 'IN-001',
                'name': 'Компьютер',
                'model': 'Dell OptiPlex',
                'manufacturer_name': 'Dell',
                'purchase_price': 100000.00,
                'current_value': 80000.00,
                'status': 'active',
                'department_code': 'IT',
                'responsible_person': 'Иванов Иван',
                'location_address': 'г. Москва, ул. Пушкина, д. 10',
                'purchase_date': '2025-01-15',
                'commissioning_date': '2025-01-20',
            },
            {
                'id': 2,
                'inventory_number': 'IN-002',
                'name': 'Принтер',
                'model': 'HP LaserJet',
                'manufacturer_name': 'HP',
                'purchase_price': 50000.00,
                'current_value': 40000.00,
                'status': 'active',
                'department_code': 'Finance',
                'responsible_person': 'Петрова Анна',
                'location_address': 'г. Москва, ул. Ленина, д. 20',
                'purchase_date': '2025-02-10',
                'commissioning_date': '2025-02-15',
            },
        ]
        
        generator = AssetReportGenerator()
        report_bytes = generator.generate(
            assets=assets,
            include_photos=include_photos,
            include_history=include_history
        )
        
        return {
            'filename': f'asset_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
            'report': report_bytes
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/assets/export")
async def export_assets(
    format: str = Query("excel", description="Формат: excel или pdf"),
    include_photos: bool = Query(False),
    include_history: bool = Query(False),
):
    """Экспорт отчета по активам в файл"""
    try:
        from backend.src.infrastructure.reports import AssetReportGenerator
        
        assets = [
            {
                'id': 1,
                'inventory_number': 'IN-001',
                'name': 'Компьютер',
                'model': 'Dell OptiPlex',
                'manufacturer_name': 'Dell',
                'purchase_price': 100000.00,
                'current_value': 80000.00,
                'status': 'active',
                'department_code': 'IT',
                'responsible_person': 'Иванов Иван',
                'location_address': 'г. Москва, ул. Пушкина, д. 10',
                'purchase_date': '2025-01-15',
                'commissioning_date': '2025-01-20',
            },
            {
                'id': 2,
                'inventory_number': 'IN-002',
                'name': 'Принтер',
                'model': 'HP LaserJet',
                'manufacturer_name': 'HP',
                'purchase_price': 50000.00,
                'current_value': 40000.00,
                'status': 'active',
                'department_code': 'Finance',
                'responsible_person': 'Петрова Анна',
                'location_address': 'г. Москва, ул. Ленина, д. 20',
                'purchase_date': '2025-02-10',
                'commissioning_date': '2025-02-15',
            },
        ]
        
        generator = AssetReportGenerator()
        report_bytes = generator.generate(
            assets=assets,
            include_photos=include_photos,
            include_history=include_history
        )
        
        filename = f'asset_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        
        if format.lower() == "pdf":
            filename += ".pdf"
            return StreamingResponse(
                iter([report_bytes]),
                media_type='application/pdf',
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            filename += ".xlsx"
            return StreamingResponse(
                iter([report_bytes]),
                media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/depreciation-report")
async def get_depreciation_report(
    report_date: Optional[str] = Query(None, description="Дата отчета (YYYY-MM-DD)"),
):
    """Отчет по амортизации - получить данные"""
    try:
        from backend.src.infrastructure.reports import DepreciationReportGenerator
        
        assets = [
            {
                'id': 1,
                'inventory_number': 'IN-001',
                'name': 'Компьютер',
                'purchase_price': 100000.00,
                'residual_value': 20000.00,
                'useful_life': 60,
                'depreciation_rate': 1.67,
                'status': 'active',
                'asset_type': 'IT',
            },
            {
                'id': 2,
                'inventory_number': 'IN-002',
                'name': 'Принтер',
                'purchase_price': 50000.00,
                'residual_value': 10000.00,
                'useful_life': 48,
                'depreciation_rate': 2.08,
                'status': 'active',
                'asset_type': 'Office',
            },
        ]
        
        generator = DepreciationReportGenerator()
        report_bytes = generator.generate(assets=assets, report_date=report_date)
        
        return {
            'filename': f'depreciation_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
            'report': report_bytes
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/depreciation/export")
async def export_depreciation(
    format: str = Query("excel", description="Формат: excel или pdf"),
    report_date: Optional[str] = Query(None),
):
    """Экспорт отчета по амортизации в файл"""
    try:
        from backend.src.infrastructure.reports import DepreciationReportGenerator
        
        assets = [
            {
                'id': 1,
                'inventory_number': 'IN-001',
                'name': 'Компьютер',
                'purchase_price': 100000.00,
                'residual_value': 20000.00,
                'useful_life': 60,
                'depreciation_rate': 1.67,
                'status': 'active',
                'asset_type': 'IT',
            },
            {
                'id': 2,
                'inventory_number': 'IN-002',
                'name': 'Принтер',
                'purchase_price': 50000.00,
                'residual_value': 10000.00,
                'useful_life': 48,
                'depreciation_rate': 2.08,
                'status': 'active',
                'asset_type': 'Office',
            },
        ]
        
        generator = DepreciationReportGenerator()
        report_bytes = generator.generate(assets=assets, report_date=report_date)
        
        filename = f'depreciation_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        
        if format.lower() == "pdf":
            filename += ".pdf"
            return StreamingResponse(
                iter([report_bytes]),
                media_type='application/pdf',
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            filename += ".xlsx"
            return StreamingResponse(
                iter([report_bytes]),
                media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/inventory-report/{check_id}")
async def get_inventory_report(check_id: int):
    """Отчет по инвентаризации - получить данные"""
    try:
        from backend.src.infrastructure.reports import InventoryReportGenerator
        
        assets = [
            {
                'id': 1,
                'inventory_number': 'IN-001',
                'name': 'Компьютер',
                'model': 'Dell OptiPlex',
                'purchase_price': 100000.00,
                'responsible_person': 'Иванов Иван',
                'location_address': 'г. Москва, ул. Пушкина, д. 10',
                'status': 'active',
            },
            {
                'id': 2,
                'inventory_number': 'IN-002',
                'name': 'Принтер',
                'model': 'HP LaserJet',
                'purchase_price': 50000.00,
                'responsible_person': 'Петрова Анна',
                'location_address': 'г. Москва, ул. Ленина, д. 20',
                'status': 'active',
            },
        ]
        
        results = [
            {
                'asset_id': 1,
                'inventory_number': 'IN-001',
                'expected_location': 'г. Москва, ул. Пушкина, д. 10',
                'actual_location': 'г. Москва, ул. Пушкина, д. 10',
                'condition': 'Хорошее',
                'notes': 'Все в порядке',
            },
        ]
        
        generator = InventoryReportGenerator()
        report_bytes = generator.generate(
            inventory_check_id=check_id,
            assets=assets,
            results=results
        )
        
        return {
            'filename': f'inventory_report_{check_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
            'report': report_bytes
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/inventory/export/{check_id}")
async def export_inventory(
    check_id: int,
    format: str = Query("excel", description="Формат: excel или pdf"),
):
    """Экспорт отчета по инвентаризации в файл"""
    try:
        from backend.src.infrastructure.reports import InventoryReportGenerator
        
        assets = [
            {
                'id': 1,
                'inventory_number': 'IN-001',
                'name': 'Компьютер',
                'model': 'Dell OptiPlex',
                'purchase_price': 100000.00,
                'responsible_person': 'Иванов Иван',
                'location_address': 'г. Москва, ул. Пушкина, д. 10',
                'status': 'active',
            },
            {
                'id': 2,
                'inventory_number': 'IN-002',
                'name': 'Принтер',
                'model': 'HP LaserJet',
                'purchase_price': 50000.00,
                'responsible_person': 'Петрова Анна',
                'location_address': 'г. Москва, ул. Ленина, д. 20',
                'status': 'active',
            },
        ]
        
        results = [
            {
                'asset_id': 1,
                'inventory_number': 'IN-001',
                'expected_location': 'г. Москва, ул. Пушкина, д. 10',
                'actual_location': 'г. Москва, ул. Пушкина, д. 10',
                'condition': 'Хорошее',
                'notes': 'Все в порядке',
            },
        ]
        
        generator = InventoryReportGenerator()
        report_bytes = generator.generate(
            inventory_check_id=check_id,
            assets=assets,
            results=results
        )
        
        filename = f'inventory_report_{check_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        
        if format.lower() == "pdf":
            filename += ".pdf"
            return StreamingResponse(
                iter([report_bytes]),
                media_type='application/pdf',
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            filename += ".xlsx"
            return StreamingResponse(
                iter([report_bytes]),
                media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/list")
async def list_reports():
    """Список доступных отчетов"""
    return {
        'reports': [
            {
                'id': 'asset',
                'name': 'Отчет по активам',
                'description': 'Сводная информация по всем активам',
                'parameters': ['include_photos', 'include_history'],
                'formats': ['excel', 'pdf']
            },
            {
                'id': 'depreciation',
                'name': 'Отчет по амортизации',
                'description': 'Информация по амортизации активов',
                'parameters': ['report_date'],
                'formats': ['excel', 'pdf']
            },
            {
                'id': 'inventory',
                'name': 'Отчет по инвентаризации',
                'description': 'Отчет по конкретной инвентаризации',
                'parameters': ['check_id'],
                'formats': ['excel', 'pdf']
            }
        ]
    }

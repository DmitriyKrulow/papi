# backend/src/presentation/http/routers/data_export.py
"""Экспорт всех данных системы в JSON-формат для полного восстановления."""
import base64
import json
import logging
import os
from datetime import datetime
from io import BytesIO
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.department import Department, Room
from src.infrastructure.db.models.employee import Employee
from src.infrastructure.db.models.asset import Asset
from src.infrastructure.db.models.document import Document
from src.infrastructure.db.models.asset_photo import AssetPhoto as AssetPhotoModel
from src.infrastructure.db.models.user import User
from src.presentation.http.dependencies.auth import get_current_admin

router = APIRouter(prefix="/api/admin/data", tags=["data-export"])

logger = logging.getLogger(__name__)


def _safe_isoformat(value: Optional[Any]) -> Optional[str]:
    """Безопасно преобразует дату в ISO-строку."""
    if value is None:
        return None
    try:
        if hasattr(value, 'isoformat') and callable(getattr(value, 'isoformat')):
            return value.isoformat()
        return str(value)
    except (AttributeError, ValueError):
        return None


def _safe_str(value: Optional[Any], default: str = "") -> str:
    """Безопасно преобразует значение в строку."""
    if value is None:
        return default
    try:
        return str(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Optional[Any], default: Optional[int] = None) -> Optional[int]:
    """Безопасно преобразует значение в int."""
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Optional[Any], default: Optional[float] = None) -> Optional[float]:
    """Безопасно преобразует значение в float."""
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ============================================================================
# Экспорт данных
# ============================================================================

def export_departments(db: Session) -> List[Dict[str, Any]]:
    """Экспортирует все подразделения."""
    departments = db.query(Department).filter(Department.is_active == True).all()
    result = []
    for dept in departments:
        result.append({
            "id": getattr(dept, 'id', None),
            "organization_id": getattr(dept, 'organization_id', 1),
            "name": _safe_str(getattr(dept, 'name', None)),
            "code": _safe_str(getattr(dept, 'code', None)),
            "parent_id": _safe_int(getattr(dept, 'parent_id', None)),
            "head": _safe_str(getattr(dept, 'head', None)),
            "phone": _safe_str(getattr(dept, 'phone', None)),
            "email": _safe_str(getattr(dept, 'email', None)),
            "location": _safe_str(getattr(dept, 'location', None)),
            "is_active": getattr(dept, 'is_active', True),
            "created_at": _safe_isoformat(getattr(dept, 'created_at', None)),
            "updated_at": _safe_isoformat(getattr(dept, 'updated_at', None)),
        })
    return result


def export_rooms(db: Session) -> List[Dict[str, Any]]:
    """Экспортирует все помещения."""
    rooms = db.query(Room).filter(Room.is_active == True).all()
    result = []
    for room in rooms:
        result.append({
            "id": getattr(room, 'id', None),
            "department_id": _safe_int(getattr(room, 'department_id', None)),
            "name": _safe_str(getattr(room, 'name', None)),
            "floor": _safe_str(getattr(room, 'floor', None)),
            "building": _safe_str(getattr(room, 'building', None)),
            "is_active": getattr(room, 'is_active', True),
            "created_at": _safe_isoformat(getattr(room, 'created_at', None)),
            "updated_at": _safe_isoformat(getattr(room, 'updated_at', None)),
        })
    return result


def export_employees(db: Session) -> List[Dict[str, Any]]:
    """Экспортирует всех сотрудников."""
    employees = db.query(Employee).filter(Employee.is_active == True).all()
    result = []
    for emp in employees:
        result.append({
            "id": getattr(emp, 'id', None),
            "department_id": _safe_int(getattr(emp, 'department_id', None)),
            "user_id": _safe_int(getattr(emp, 'user_id', None)),
            "first_name": _safe_str(getattr(emp, 'first_name', None)),
            "last_name": _safe_str(getattr(emp, 'last_name', None)),
            "middle_name": _safe_str(getattr(emp, 'middle_name', None)),
            "phone": _safe_str(getattr(emp, 'phone', None)),
            "email": _safe_str(getattr(emp, 'email', None)),
            "position": _safe_str(getattr(emp, 'position', None)),
            "position_code": _safe_str(getattr(emp, 'position_code', None)),
            "employee_number": _safe_str(getattr(emp, 'employee_number', None)),
            "hire_date": _safe_isoformat(getattr(emp, 'hire_date', None)),
            "termination_date": _safe_isoformat(getattr(emp, 'termination_date', None)),
            "is_active": getattr(emp, 'is_active', True),
            "created_at": _safe_isoformat(getattr(emp, 'created_at', None)),
            "updated_at": _safe_isoformat(getattr(emp, 'updated_at', None)),
        })
    return result


def export_assets(db: Session) -> List[Dict[str, Any]]:
    """Экспортирует все активы."""
    assets = db.query(Asset).options(joinedload(Asset.asset_type_config)).all()
    result = []
    for asset in assets:
        result.append({
            "id": getattr(asset, 'id', None),
            "inventory_number": _safe_str(getattr(asset, 'inventory_number', None)),
            "name": _safe_str(getattr(asset, 'name', None)),
            "description": _safe_str(getattr(asset, 'description', None)),
            "model": _safe_str(getattr(asset, 'model', None)),
            "asset_type": _safe_str(getattr(asset, 'asset_type', None)),
            "status": _safe_str(getattr(asset, 'status', None)),
            "purchase_price": _safe_float(getattr(asset, 'purchase_price', None)),
            "current_value": _safe_float(getattr(asset, 'current_value', None)),
            "quantity": _safe_int(getattr(asset, 'quantity', None), 1),
            "department_code": _safe_str(getattr(asset, 'department_code', None)),
            "responsible_person": _safe_str(getattr(asset, 'responsible_person', None)),
            "location_address": _safe_str(getattr(asset, 'location_address', None)),
            "manufacturer_code": _safe_str(getattr(asset, 'manufacturer_code', None)),
            "manufacturer_name": _safe_str(getattr(asset, 'manufacturer_name', None)),
            "purchase_date": _safe_isoformat(getattr(asset, 'purchase_date', None)),
            "commissioning_date": _safe_isoformat(getattr(asset, 'commissioning_date', None)),
            "warranty_expiry": _safe_isoformat(getattr(asset, 'warranty_expiry', None)),
            "serial_number": _safe_str(getattr(asset, 'serial_number', None)),
            "capacity": _safe_float(getattr(asset, 'capacity', None)),
            "power": _safe_str(getattr(asset, 'power', None)),
            "weight": _safe_str(getattr(asset, 'weight', None)),
            "consumable_type": _safe_str(getattr(asset, 'consumable_type', None)),
            "crypto_wallet_address": _safe_str(getattr(asset, 'crypto_wallet_address', None)),
            "crypto_token_symbol": _safe_str(getattr(asset, 'crypto_token_symbol', None)),
            "depreciation_years": _safe_int(getattr(asset, 'depreciation_years', None)),
            "next_maintenance_date": _safe_isoformat(getattr(asset, 'next_maintenance_date', None)),
            "created_at": _safe_isoformat(getattr(asset, 'created_at', None)),
            "updated_at": _safe_isoformat(getattr(asset, 'updated_at', None)),
            "is_active": getattr(asset, 'is_active', True),
            "last_inventory_date": _safe_isoformat(getattr(asset, 'last_inventory_date', None)),
            "last_inventory_by_id": _safe_int(getattr(asset, 'last_inventory_by_id', None)),
            "last_inventory_confirmed": getattr(asset, 'last_inventory_confirmed', False),
            "employee_id": _safe_int(getattr(asset, 'employee_id', None)),
            "room_id": _safe_int(getattr(asset, 'room_id', None)),
        })
    return result


def export_documents(db: Session) -> List[Dict[str, Any]]:
    """Экспортирует все документы с содержимым файлов в base64."""
    documents = db.query(Document).all()
    result = []
    for doc in documents:
        doc_data = {
            "id": getattr(doc, 'id', None),
            "filename": _safe_str(getattr(doc, 'filename', None)),
            "file_path": _safe_str(getattr(doc, 'file_path', None)),
            "file_size": _safe_int(getattr(doc, 'file_size', None)),
            "mime_type": _safe_str(getattr(doc, 'mime_type', None)),
            "document_type": _safe_str(getattr(doc, 'document_type', None)),
            "category": _safe_str(getattr(doc, 'category', None)),
            "entity_id": _safe_int(getattr(doc, 'entity_id', None)),
            "entity_type": _safe_str(getattr(doc, 'entity_type', None)),
            "title": _safe_str(getattr(doc, 'title', None)),
            "description": _safe_str(getattr(doc, 'description', None)),
            "uploaded_by": _safe_int(getattr(doc, 'uploaded_by', None)),
            "uploaded_at": _safe_isoformat(getattr(doc, 'uploaded_at', None)),
            "is_primary": getattr(doc, 'is_primary', False),
            "sort_order": _safe_int(getattr(doc, 'sort_order', None)),
            "file_hash": _safe_str(getattr(doc, 'file_hash', None)),
            "file_content": None,  # Заполняется ниже
        }
        
        # Читаем файл и кодируем в base64
        file_path = str(doc.file_path)
        if os.path.exists(file_path):
            try:
                with open(file_path, "rb") as f:
                    file_bytes = f.read()
                # Кодируем в base64 для включения в JSON
                doc_data["file_content"] = base64.b64encode(file_bytes).decode('utf-8')
                doc_data["file_size_exported"] = len(file_bytes)
            except Exception as e:
                logger.warning(f"[DataExport] Could not read file {file_path}: {e}")
                doc_data["file_content"] = None
        else:
            logger.warning(f"[DataExport] File not found on disk: {file_path}")
            doc_data["file_content"] = None
        
        result.append(doc_data)
    
    return result


def export_asset_photos(db: Session) -> List[Dict[str, Any]]:
    """Экспортирует все фотографии активов."""
    photos = db.query(AssetPhotoModel).all()
    result = []
    for photo in photos:
        result.append({
            "id": getattr(photo, 'id', None),
            "asset_id": _safe_int(getattr(photo, 'asset_id', None)),
            "document_id": _safe_int(getattr(photo, 'document_id', None)),
            "uploaded_by": _safe_int(getattr(photo, 'uploaded_by', None)),
            "stage": _safe_str(getattr(photo, 'stage', None)),
            "photo_category": _safe_str(getattr(photo, 'photo_category', None)),
            "description": _safe_str(getattr(photo, 'description', None)),
            "taken_at": _safe_isoformat(getattr(photo, 'taken_at', None)),
            "taken_by": _safe_int(getattr(photo, 'taken_by', None)),
            "uploaded_at": _safe_isoformat(getattr(photo, 'uploaded_at', None)),
            "inventory_check_id": _safe_int(getattr(photo, 'inventory_check_id', None)),
            "repair_request_id": _safe_int(getattr(photo, 'repair_request_id', None)),
            "is_before": getattr(photo, 'is_before', False),
            "is_after": getattr(photo, 'is_after', False),
            "sort_order": _safe_int(getattr(photo, 'sort_order', None)),
        })
    return result


@router.get("/export/all")
async def export_all_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Экспортирует все данные системы в JSON-формате.
    Включает: подразделения, помещения, сотрудников, активы, документы (с файлами), фотографии.
    
    Формат файла:
    {
      "exported_at": "2026-08-12T20:00:00",
      "version": "2.0",
      "departments": [...],
      "rooms": [...],
      "employees": [...],
      "assets": [...],
      "documents": [...],  // файлы в base64
      "asset_photos": [...]  // метаданные фотографий
    }
    """
    try:
        logger.info(f"[DataExport] Starting full export by user: {current_user.username}")
        
        data = {
            "exported_at": datetime.now().isoformat(),
            "version": "2.0",
            "departments": export_departments(db),
            "rooms": export_rooms(db),
            "employees": export_employees(db),
            "assets": export_assets(db),
            "documents": export_documents(db),
            "asset_photos": export_asset_photos(db),
        }
        
        doc_count = len(data['documents'])
        photo_count = len(data['asset_photos'])
        docs_with_content = sum(1 for d in data['documents'] if d.get('file_content'))
        
        logger.info(f"[DataExport] Exported: {len(data['departments'])} depts, "
                    f"{len(data['rooms'])} rooms, {len(data['employees'])} employees, "
                    f"{len(data['assets'])} assets, "
                    f"{doc_count} documents ({docs_with_content} with content), "
                    f"{photo_count} photos")
        
        # Создаём JSON-файл для скачивания
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        
        output = BytesIO(json_str.encode('utf-8'))
        
        filename = f"papi_full_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        return StreamingResponse(
            iter([output.read()]),
            media_type='application/json',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
        
    except Exception as e:
        logger.error(f"[DataExport] Export failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Импорт/восстановление данных
# ============================================================================

# ============================================================================
# Импорт/восстановление данных
# ============================================================================

def import_documents(db: Session, documents_data: List[Dict[str, Any]], uploads_base_dir: str = "uploads") -> Dict[str, int]:
    """Импортирует документы и восстанавливает файлы на диске."""
    imported = 0
    skipped = 0
    errors = []
    files_created = 0
    files_failed = 0
    
    for doc_data in documents_data:
        try:
            # Проверяем, есть ли содержимое файла
            file_content_b64 = doc_data.get("file_content")
            file_path = doc_data.get("file_path", "")
            filename = doc_data.get("filename", "")
            
            if file_content_b64:
                # Декодируем base64 и сохраняем файл
                try:
                    file_bytes = base64.b64decode(file_content_b64)
                    
                    # Создаём директорию если нужно
                    doc_dir = os.path.dirname(file_path)
                    if doc_dir and not os.path.exists(doc_dir):
                        os.makedirs(doc_dir, exist_ok=True)
                    
                    # Сохраняем файл
                    with open(file_path, "wb") as f:
                        f.write(file_bytes)
                    files_created += 1
                    
                except Exception as e:
                    logger.warning(f"[DataImport] Could not save file {file_path}: {e}")
                    skipped += 1
                    errors.append(f"Document '{filename}': Failed to save file - {str(e)}")
                    continue
            
            # Создаём запись в БД
            document = Document(
                filename=filename,
                file_path=file_path,
                file_size=doc_data.get("file_size", 0),
                mime_type=doc_data.get("mime_type", "application/octet-stream"),
                document_type=doc_data.get("document_type", "other"),
                category=doc_data.get("category", "asset"),
                entity_id=doc_data.get("entity_id"),
                entity_type=doc_data.get("entity_type"),
                title=doc_data.get("title"),
                description=doc_data.get("description"),
                uploaded_by=doc_data.get("uploaded_by", 0),
                uploaded_at=datetime.fromisoformat(doc_data["uploaded_at"]) if doc_data.get("uploaded_at") else datetime.now(),
                is_primary=doc_data.get("is_primary", False),
                sort_order=doc_data.get("sort_order", 0),
                file_hash=doc_data.get("file_hash"),
            )
            db.add(document)
            imported += 1
            
        except Exception as e:
            skipped += 1
            errors.append(f"Document '{doc_data.get('filename', '?')}': {str(e)}")
    
    return {
        "imported": imported,
        "skipped": skipped,
        "errors": errors,
        "files_created": files_created,
        "files_failed": files_failed,
    }


def import_asset_photos(db: Session, photos_data: List[Dict[str, Any]]) -> Dict[str, int]:
    """Импортирует фотографии активов."""
    imported = 0
    skipped = 0
    errors = []
    
    for photo_data in photos_data:
        try:
            photo = AssetPhotoModel(
                asset_id=photo_data.get("asset_id"),
                document_id=photo_data.get("document_id"),
                uploaded_by=photo_data.get("uploaded_by", 0),
                stage=photo_data.get("stage", "other"),
                photo_category=photo_data.get("photo_category"),
                description=photo_data.get("description"),
                uploaded_at=datetime.fromisoformat(photo_data["uploaded_at"]) if photo_data.get("uploaded_at") else datetime.now(),
                inventory_check_id=photo_data.get("inventory_check_id"),
                repair_request_id=photo_data.get("repair_request_id"),
                is_before=photo_data.get("is_before", False),
                is_after=photo_data.get("is_after", False),
                sort_order=photo_data.get("sort_order", 0),
            )
            # Парсим taken_at если есть
            if photo_data.get("taken_at"):
                try:
                    photo.taken_at = datetime.fromisoformat(photo_data["taken_at"])
                except:
                    pass
            
            db.add(photo)
            imported += 1
            
        except Exception as e:
            skipped += 1
            errors.append(f"Photo (asset_id={photo_data.get('asset_id')}): {str(e)}")
    
    return {
        "imported": imported,
        "skipped": skipped,
        "errors": errors,
    }


@router.post("/import/all")
async def import_all_data(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Восстанавливает все данные системы из JSON-файла экспорта.
    
    Порядок восстановления:
    1. Подразделения (зависят только от organization_id)
    2. Помещения (зависят от departments)
    3. Сотрудники (зависят от departments)
    4. Активы (зависят от departments, employees)
    5. Документы и файлы (зависят от путей на диске)
    6. Фотографии активов (зависят от assets и documents)
    
    Все существующие данные удаляются перед восстановлением.
    """
    try:
        body = await request.body()
        if not body:
            raise HTTPException(status_code=400, detail="Файл не передан")
        
        # Парсим JSON
        data = json.loads(body.decode('utf-8'))
        
        if not isinstance(data, dict):
            raise HTTPException(status_code=400, detail="Неверный формат файла")
        
        # Проверяем обязательные секции
        required_sections = ["departments", "rooms", "employees", "assets"]
        for section in required_sections:
            if section not in data:
                raise HTTPException(status_code=400, detail=f"Отсутствует раздел: {section}")
        
        logger.info(f"[DataImport] Starting full import by user: {current_user.username}")
        logger.info(f"[DataImport] Sections: depts={len(data['departments'])}, "
                    f"rooms={len(data['rooms'])}, employees={len(data['employees'])}, "
                    f"assets={len(data['assets'])}")
        
        # Добавляем секции документов и фотографий если есть
        has_documents = "documents" in data
        has_photos = "asset_photos" in data
        
        if has_documents:
            logger.info(f"[DataImport] Documents: {len(data['documents'])}")
        if has_photos:
            logger.info(f"[DataImport] Asset photos: {len(data['asset_photos'])}")
        
        stats = {
            "departments": {"imported": 0, "skipped": 0, "errors": []},
            "rooms": {"imported": 0, "skipped": 0, "errors": []},
            "employees": {"imported": 0, "skipped": 0, "errors": []},
            "assets": {"imported": 0, "skipped": 0, "errors": []},
        }
        
        if has_documents:
            stats["documents"] = {"imported": 0, "skipped": 0, "errors": [], "files_created": 0}
        if has_photos:
            stats["asset_photos"] = {"imported": 0, "skipped": 0, "errors": []}
        
        # Маппинг: старый ID -> новый ID для подразделений
        dept_id_map: Dict[int, int] = {}
        
        # Очистка существующих данных (в обратном порядке зависимостей)
        logger.info("[DataImport] Clearing existing data...")
        from src.infrastructure.db.models.asset import Asset as AssetModel
        db.query(AssetModel).delete()
        db.query(Employee).delete()
        db.query(Room).delete()
        db.query(Department).delete()
        
        # Очищаем документы и фотографии если есть в экспорте
        if has_photos:
            db.query(AssetPhotoModel).delete()
        if has_documents:
            # Удаляем файлы с диска
            documents_to_delete = db.query(Document).all()
            for doc in documents_to_delete:
                file_path = str(doc.file_path)
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.debug(f"[DataImport] Deleted file: {file_path}")
                except Exception as e:
                    logger.warning(f"[DataImport] Could not delete file {file_path}: {e}")
            db.query(Document).delete()
        
        db.commit()
        
        # 1. Восстанавливаем подразделения
        logger.info("[DataImport] Restoring departments...")
        for dept_data in data.get("departments", []):
            try:
                dept = Department(
                    organization_id=dept_data.get("organization_id", 1),
                    name=dept_data.get("name", ""),
                    code=dept_data.get("code", ""),
                    parent_id=dept_data.get("parent_id"),
                    head=dept_data.get("head"),
                    phone=dept_data.get("phone"),
                    email=dept_data.get("email"),
                    location=dept_data.get("location"),
                    is_active=dept_data.get("is_active", True),
                    created_at=datetime.fromisoformat(dept_data["created_at"]) if dept_data.get("created_at") else datetime.now(),
                    updated_at=datetime.fromisoformat(dept_data["updated_at"]) if dept_data.get("updated_at") else datetime.now(),
                )
                db.add(dept)
                db.flush()  # Получаем новый ID
                old_id = dept_data.get("id")
                if old_id is not None:
                    dept_id_map[old_id] = dept.id
                stats["departments"]["imported"] += 1
            except Exception as e:
                stats["departments"]["skipped"] += 1
                stats["departments"]["errors"].append(f"Department '{dept_data.get('code', '?')}': {str(e)}")
        
        db.commit()
        
        # 2. Восстанавливаем помещения (с маппингом department_id)
        logger.info("[DataImport] Restoring rooms...")
        for room_data in data.get("rooms", []):
            try:
                old_dept_id = room_data.get("department_id")
                # Используем маппинг, если старый ID известен, иначе оставляем как есть
                new_dept_id = dept_id_map.get(old_dept_id, old_dept_id) if old_dept_id is not None else None
                
                room = Room(
                    department_id=new_dept_id,
                    name=room_data.get("name", ""),
                    floor=room_data.get("floor"),
                    building=room_data.get("building"),
                    is_active=room_data.get("is_active", True),
                    created_at=datetime.fromisoformat(room_data["created_at"]) if room_data.get("created_at") else datetime.now(),
                    updated_at=datetime.fromisoformat(room_data["updated_at"]) if room_data.get("updated_at") else datetime.now(),
                )
                db.add(room)
                stats["rooms"]["imported"] += 1
            except Exception as e:
                stats["rooms"]["skipped"] += 1
                stats["rooms"]["errors"].append(f"Room '{room_data.get('name', '?')}': {str(e)}")
        
        db.commit()
        
        # Маппинг ID для сотрудников
        emp_id_map: Dict[int, int] = {}
        
        # 3. Восстанавливаем сотрудников
        logger.info("[DataImport] Restoring employees...")
        for emp_data in data.get("employees", []):
            try:
                old_dept_id = emp_data.get("department_id")
                new_dept_id = dept_id_map.get(old_dept_id, old_dept_id) if old_dept_id is not None else None
                
                emp = Employee(
                    department_id=new_dept_id,
                    user_id=emp_data.get("user_id"),
                    first_name=emp_data.get("first_name", ""),
                    last_name=emp_data.get("last_name", ""),
                    middle_name=emp_data.get("middle_name"),
                    phone=emp_data.get("phone"),
                    email=emp_data.get("email"),
                    position=emp_data.get("position"),
                    position_code=emp_data.get("position_code"),
                    employee_number=emp_data.get("employee_number") or None,
                    hire_date=datetime.fromisoformat(emp_data["hire_date"]).date() if emp_data.get("hire_date") else None,
                    termination_date=datetime.fromisoformat(emp_data["termination_date"]).date() if emp_data.get("termination_date") else None,
                    is_active=emp_data.get("is_active", True),
                    created_at=datetime.fromisoformat(emp_data["created_at"]) if emp_data.get("created_at") else datetime.now(),
                    updated_at=datetime.fromisoformat(emp_data["updated_at"]) if emp_data.get("updated_at") else datetime.now(),
                )
                db.add(emp)
                db.flush()
                old_id = emp_data.get("id")
                if old_id is not None:
                    emp_id_map[old_id] = emp.id
                stats["employees"]["imported"] += 1
            except Exception as e:
                stats["employees"]["skipped"] += 1
                stats["employees"]["errors"].append(f"Employee '{emp_data.get('last_name', '?')}': {str(e)}")
        
        db.commit()
        
        # Маппинг ID для помещений
        room_id_map: Dict[int, int] = {}
        
        # 4. Восстанавливаем активы
        logger.info("[DataImport] Restoring assets...")
        from datetime import date
        for asset_data in data.get("assets", []):
            try:
                # Парсим даты
                purchase_date = None
                if asset_data.get("purchase_date"):
                    try:
                        purchase_date = datetime.fromisoformat(asset_data["purchase_date"]).date()
                    except:
                        pass
                
                commissioning_date = None
                if asset_data.get("commissioning_date"):
                    try:
                        commissioning_date = datetime.fromisoformat(asset_data["commissioning_date"]).date()
                    except:
                        pass
                
                warranty_expiry = None
                if asset_data.get("warranty_expiry"):
                    try:
                        warranty_expiry = datetime.fromisoformat(asset_data["warranty_expiry"]).date()
                    except:
                        pass
                
                next_maintenance_date = None
                if asset_data.get("next_maintenance_date"):
                    try:
                        next_maintenance_date = datetime.fromisoformat(asset_data["next_maintenance_date"]).date()
                    except:
                        pass
                
                last_inventory_date = None
                if asset_data.get("last_inventory_date"):
                    try:
                        last_inventory_date = datetime.fromisoformat(asset_data["last_inventory_date"])
                    except:
                        pass
                
                # Маппинг ID для employee и room
                old_emp_id = asset_data.get("employee_id")
                new_emp_id = emp_id_map.get(old_emp_id, old_emp_id) if old_emp_id is not None else None
                
                old_room_id = asset_data.get("room_id")
                new_room_id = room_id_map.get(old_room_id, old_room_id) if old_room_id is not None else None
                
                from decimal import Decimal
                asset = Asset(
                    inventory_number=asset_data.get("inventory_number", ""),
                    name=asset_data.get("name", ""),
                    description=asset_data.get("description"),
                    model=asset_data.get("model"),
                    asset_type=asset_data.get("asset_type"),
                    status=asset_data.get("status", "active"),
                    purchase_price=Decimal(str(asset_data["purchase_price"])) if asset_data.get("purchase_price") is not None else Decimal("0"),
                    current_value=Decimal(str(asset_data["current_value"])) if asset_data.get("current_value") is not None else Decimal("0"),
                    quantity=asset_data.get("quantity", 1),
                    department_code=asset_data.get("department_code"),
                    responsible_person=asset_data.get("responsible_person"),
                    location_address=asset_data.get("location_address"),
                    manufacturer_code=asset_data.get("manufacturer_code"),
                    manufacturer_name=asset_data.get("manufacturer_name"),
                    purchase_date=purchase_date,
                    commissioning_date=commissioning_date,
                    warranty_expiry=warranty_expiry,
                    serial_number=asset_data.get("serial_number"),
                    capacity=Decimal(str(asset_data["capacity"])) if asset_data.get("capacity") is not None else None,
                    power=asset_data.get("power"),
                    weight=asset_data.get("weight"),
                    consumable_type=asset_data.get("consumable_type"),
                    crypto_wallet_address=asset_data.get("crypto_wallet_address"),
                    crypto_token_symbol=asset_data.get("crypto_token_symbol"),
                    depreciation_years=asset_data.get("depreciation_years"),
                    next_maintenance_date=next_maintenance_date,
                    created_at=datetime.fromisoformat(asset_data["created_at"]) if asset_data.get("created_at") else datetime.now(),
                    updated_at=datetime.fromisoformat(asset_data["updated_at"]) if asset_data.get("updated_at") else datetime.now(),
                    is_active=asset_data.get("is_active", True),
                    last_inventory_date=last_inventory_date,
                    last_inventory_by_id=asset_data.get("last_inventory_by_id"),
                    last_inventory_confirmed=asset_data.get("last_inventory_confirmed", False),
                    employee_id=new_emp_id,
                    room_id=new_room_id,
                )
                db.add(asset)
                stats["assets"]["imported"] += 1
            except Exception as e:
                stats["assets"]["skipped"] += 1
                stats["assets"]["errors"].append(f"Asset '{asset_data.get('inventory_number', '?')}': {str(e)}")
        
        db.commit()
        
        # 5. Восстанавливаем документы и файлы
        doc_import_stats = {"imported": 0, "skipped": 0, "errors": [], "files_created": 0}
        if has_documents:
            logger.info("[DataImport] Restoring documents and files...")
            doc_import_stats = import_documents(db, data["documents"])
            stats["documents"] = {
                "imported": doc_import_stats["imported"],
                "skipped": doc_import_stats["skipped"],
                "errors": doc_import_stats["errors"],
                "files_created": doc_import_stats["files_created"],
            }
            logger.info(f"[DataImport] Documents imported: {doc_import_stats['imported']}, "
                       f"files created: {doc_import_stats['files_created']}")
        
        db.commit()
        
        # 6. Восстанавливаем фотографии активов
        photo_import_stats = {"imported": 0, "skipped": 0, "errors": []}
        if has_photos:
            logger.info("[DataImport] Restoring asset photos...")
            photo_import_stats = import_asset_photos(db, data["asset_photos"])
            stats["asset_photos"] = {
                "imported": photo_import_stats["imported"],
                "skipped": photo_import_stats["skipped"],
                "errors": photo_import_stats["errors"],
            }
            logger.info(f"[DataImport] Asset photos imported: {photo_import_stats['imported']}")
        
        db.commit()
        
        total_imported = sum(s["imported"] for s in stats.values())
        total_skipped = sum(s["skipped"] for s in stats.values())
        
        logger.info(f"[DataImport] Import completed: imported={total_imported}, skipped={total_skipped}")
        
        return {
            "message": f"Данные восстановлены: импортировано {total_imported}, пропущено {total_skipped}",
            "imported": total_imported,
            "skipped": total_skipped,
            "stats": stats,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[DataImport] Import failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

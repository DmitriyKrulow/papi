# backend/src/presentation/http/routers/regulatory_documents.py
"""Нормативные документы — оснащение, должностные обязанности, ответственность"""
import logging
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.regulatory_document import (
    RegulatoryDocument, EquipmentStandard, ResponsibilityRecord
)
from src.infrastructure.db.models.asset import Asset
from src.infrastructure.db.models.employee import Employee
from src.infrastructure.db.models.department import Department
from src.infrastructure.db.models.user import User
from src.presentation.http.dependencies.auth import get_current_user, get_current_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/regulatory", tags=["regulatory-documents"])


# ======================================================================
# Нормативные документы
# ======================================================================

@router.get("/documents")
async def list_documents(
    doc_type: Optional[str] = Query(None, description="Тип документа"),
    is_active: bool = Query(True, description="Только активные"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Список нормативных документов"""
    query = db.query(RegulatoryDocument)
    if doc_type:
        query = query.filter(RegulatoryDocument.doc_type == doc_type)
    if is_active:
        query = query.filter(RegulatoryDocument.is_active == True)
    
    docs = query.order_by(RegulatoryDocument.document_date.desc()).all()
    
    return {
        "documents": [
            {
                "id": d.id,
                "title": d.title,
                "doc_type": d.doc_type,
                "document_number": d.document_number or "",
                "document_date": d.document_date.isoformat() if d.document_date else None,
                "applies_to_type": d.applies_to_type or "",
                "applies_to_id": d.applies_to_id,
                "is_published": d.is_published,
                "is_active": d.is_active,
                "author_name": d.author.full_name if d.author else None,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in docs
        ],
        "total": len(docs),
    }


@router.post("/documents")
async def create_document(
    title: str = Query(...),
    doc_type: str = Query(...),
    document_number: str = Query(""),
    document_date: str = Query(""),
    applies_to_type: str = Query(""),
    applies_to_id: Optional[int] = None,
    content: str = Query(""),
    file_path: str = Query(""),
    file_name: str = Query(""),
    is_published: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Создать нормативный документ"""
    try:
        doc_date = datetime.fromisoformat(document_date) if document_date else None
    except ValueError:
        doc_date = None
    
    doc = RegulatoryDocument(
        title=title,
        doc_type=doc_type,
        document_number=document_number,
        document_date=doc_date,
        applies_to_type=applies_to_type,
        applies_to_id=applies_to_id,
        content=content,
        file_path=file_path,
        file_name=file_name,
        is_published=is_published,
        author_id=current_user.id,
    )
    
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    return {"success": True, "id": doc.id, "title": doc.title}


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Удалить документ (мягкое удаление)"""
    doc = db.query(RegulatoryDocument).filter(RegulatoryDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Документ не найден")
    
    doc.is_active = False
    db.commit()
    
    return {"success": True, "message": "Документ удалён"}


# ======================================================================
# Нормативы оснащения
# ======================================================================

@router.get("/equipment-standards")
async def list_equipment_standards(
    position_code: Optional[str] = Query(None, description="Код должности"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Нормативы оснащения по должностям"""
    query = db.query(EquipmentStandard).filter(EquipmentStandard.is_active == True)
    if position_code:
        query = query.filter(EquipmentStandard.position_code == position_code)
    
    standards = query.order_by(EquipmentStandard.position_code, EquipmentStandard.priority).all()
    
    return {
        "standards": [
            {
                "id": s.id,
                "position_code": s.position_code,
                "position_name": s.position_name,
                "asset_type_code": s.asset_type_code,
                "asset_type_name": s.asset_type_name,
                "quantity": s.quantity,
                "priority": s.priority,
            }
            for s in standards
        ],
        "total": len(standards),
    }


@router.post("/equipment-standards")
async def create_equipment_standard(
    position_code: str = Query(...),
    position_name: str = Query(...),
    asset_type_code: str = Query(...),
    asset_type_name: str = Query(...),
    quantity: int = Query(1),
    priority: int = Query(1),
    description: str = Query(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Создать норматив оснащения"""
    standard = EquipmentStandard(
        position_code=position_code,
        position_name=position_name,
        asset_type_code=asset_type_code,
        asset_type_name=asset_type_name,
        quantity=quantity,
        priority=priority,
        description=description,
    )
    
    db.add(standard)
    db.commit()
    db.refresh(standard)
    
    return {"success": True, "id": standard.id}


@router.get("/compliance/{employee_id}")
async def check_compliance(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Проверка соответствия оснащению.
    
    Сравнивает фактическое имущество сотрудника с нормативами.
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")
    
    # Получаем нормативы для должности
    standards = db.query(EquipmentStandard).filter(
        EquipmentStandard.position_code == employee.position_code,
        EquipmentStandard.is_active == True,
    ).all()
    
    # Получаем фактическое имущество сотрудника
    assets = db.query(Asset).filter(
        Asset.employee_id == employee_id,
        Asset.is_active == True,
    ).all()
    
    # Группируем фактическое имущество по типам
    actual_by_type = {}
    for a in assets:
        code = a.asset_type or "unknown"
        if code not in actual_by_type:
            actual_by_type[code] = 0
        actual_by_type[code] += 1
    
    # Сравниваем с нормативами
    compliance = []
    for s in standards:
        actual = actual_by_type.get(s.asset_type_code, 0)
        expected = s.quantity
        status = "ok" if actual >= expected else ("partial" if actual > 0 else "missing")
        
        compliance.append({
            "asset_type": s.asset_type_name,
            "expected": expected,
            "actual": actual,
            "status": status,
            "deficit": max(0, expected - actual),
        })
    
    # Подсчитываем общий процент соответствия
    total_standards = len(compliance)
    met_standards = sum(1 for c in compliance if c["status"] == "ok")
    compliance_percent = round(met_standards / total_standards * 100, 1) if total_standards > 0 else 100
    
    return {
        "employee_id": employee.id,
        "full_name": f"{employee.last_name} {employee.first_name}",
        "position": employee.position,
        "department": employee.department.name if employee.department else "",
        "compliance_percent": compliance_percent,
        "standards_met": met_standards,
        "total_standards": total_standards,
        "compliance": compliance,
    }


# ======================================================================
# Записи ответственности
# ======================================================================

@router.get("/responsibilities")
async def list_responsibilities(
    department_id: Optional[int] = None,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Список записей ответственности"""
    query = db.query(ResponsibilityRecord).filter(
        ResponsibilityRecord.is_active == True
    )
    if department_id:
        query = query.filter(ResponsibilityRecord.department_id == department_id)
    if employee_id:
        query = query.filter(ResponsibilityRecord.employee_id == employee_id)
    
    records = query.order_by(ResponsibilityRecord.assigned_date.desc()).all()
    
    return {
        "responsibilities": [
            {
                "id": r.id,
                "employee_id": r.employee_id,
                "employee_name": f"{r.employee.last_name} {r.employee.first_name}" if r.employee else "",
                "department_id": r.department_id,
                "department_name": r.department.name if r.department else "",
                "responsibility_type": r.responsibility_type,
                "responsibility_level": r.responsibility_level,
                "assigned_date": r.assigned_date.isoformat() if r.assigned_date else None,
                "end_date": r.end_date.isoformat() if r.end_date else None,
                "document_number": r.document_number or "",
                "comment": r.comment or "",
            }
            for r in records
        ],
        "total": len(records),
    }


@router.post("/responsibilities")
async def create_responsibility(
    employee_id: int = Query(...),
    department_id: Optional[int] = None,
    responsibility_type: str = Query("full"),
    asset_ids: str = Query(""),  # JSON
    responsibility_level: str = Query("full"),
    document_number: str = Query(""),
    document_date: str = Query(""),
    comment: str = Query(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Создать запись ответственности"""
    record = ResponsibilityRecord(
        employee_id=employee_id,
        department_id=department_id,
        responsibility_type=responsibility_type,
        asset_ids=asset_ids,
        responsibility_level=responsibility_level,
        document_number=document_number,
        document_date=datetime.fromisoformat(document_date) if document_date else None,
        comment=comment,
    )
    
    db.add(record)
    db.commit()
    db.refresh(record)
    
    return {"success": True, "id": record.id}


@router.get("/stats")
async def get_regulatory_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Статистика по нормативным документам"""
    total_docs = db.query(func.count(RegulatoryDocument.id)).filter(
        RegulatoryDocument.is_active == True
    ).scalar() or 0
    
    published_docs = db.query(func.count(RegulatoryDocument.id)).filter(
        RegulatoryDocument.is_active == True,
        RegulatoryDocument.is_published == True,
    ).scalar() or 0
    
    total_standards = db.query(func.count(EquipmentStandard.id)).filter(
        EquipmentStandard.is_active == True
    ).scalar() or 0
    
    active_responsibilities = db.query(func.count(ResponsibilityRecord.id)).filter(
        ResponsibilityRecord.is_active == True
    ).scalar() or 0
    
    return {
        "total_documents": total_docs,
        "published_documents": published_docs,
        "equipment_standards": total_standards,
        "active_responsibilities": active_responsibilities,
    }

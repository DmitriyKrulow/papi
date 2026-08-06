# backend/src/presentation/http/routers/placement_assignments.py
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session, joinedload
from typing import Optional, Any
from datetime import datetime

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.asset import Asset
from src.infrastructure.db.models.department import Department, Room
from src.infrastructure.db.models.employee import Employee
from src.infrastructure.db.models.user import User
from src.presentation.http.dependencies.auth import get_current_admin

router = APIRouter(prefix="/admin/placement-assignments", tags=["placement-assignments"])


def safe_isoformat(value: Optional[Any]) -> Optional[str]:
    if value is None:
        return None
    try:
        if hasattr(value, 'isoformat') and callable(getattr(value, 'isoformat')):
            return value.isoformat()
        return str(value)
    except (AttributeError, ValueError):
        return None


def safe_str(value: Optional[Any], default: str = "") -> str:
    if value is None:
        return default
    try:
        return str(value)
    except (TypeError, ValueError):
        return default


def assignment_to_dict(asset, dept_name: str = "", emp_name: str = "", location: str = ""):
    return {
        "id": getattr(asset, 'id', None),
        "inventory_number": safe_str(getattr(asset, 'inventory_number', None)),
        "name": safe_str(getattr(asset, 'name', None)),
        "model": safe_str(getattr(asset, 'model', None)),
        "asset_type": safe_str(getattr(asset, 'asset_type', None)),
        "status": safe_str(getattr(asset, 'status', None)),
        "department_code": safe_str(getattr(asset, 'department_code', None)),
        "department_name": safe_str(dept_name),
        "responsible_person": safe_str(getattr(asset, 'responsible_person', None)),
        "employee_name": safe_str(emp_name),
        "location_address": safe_str(location),
        "created_at": safe_isoformat(getattr(asset, 'created_at', None)),
        "updated_at": safe_isoformat(getattr(asset, 'updated_at', None)),
    }


@router.get("/departments")
async def get_available_departments(
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    query = db.query(Department).filter(Department.is_active == True)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Department.name.ilike(search_pattern)) | 
            (Department.code.ilike(search_pattern))
        )
    
    departments = query.order_by(Department.name).all()
    
    return [
        {
            "id": d.id,
            "name": d.name,
            "code": d.code,
            "location": d.location or "",
            "head": d.head or "",
            "full_name": f"{d.name} ({d.code})" if d.code else d.name,
        }
        for d in departments
    ]


@router.get("/responsible-persons")
async def get_responsible_persons(
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    query = db.query(User).filter(
        User.is_active == True,
        User.role.in_(["admin", "responsible"])
    )
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (User.username.ilike(search_pattern)) |
            (User.full_name.ilike(search_pattern))
        )
    
    users = query.order_by(User.username).all()
    
    return [
        {
            "id": u.id,
            "name": safe_str(getattr(u, 'full_name', None)) or safe_str(getattr(u, 'username', None)),
            "full_name": safe_str(getattr(u, 'full_name', None)) or safe_str(getattr(u, 'username', None)),
            "username": safe_str(getattr(u, 'username', None)),
            "role": safe_str(getattr(u, 'role', None)),
        }
        for u in users
    ]


@router.get("/employees")
async def get_available_employees(
    search: Optional[str] = None,
    department_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    query = db.query(Employee).options(
        joinedload(Employee.department),
        joinedload(Employee.user)
    ).join(User, isouter=True).filter(
        Employee.is_active == True,
        (User.role.in_(["admin", "responsible"])) | (User.id.is_(None))
    )

    if department_id:
        query = query.filter(Employee.department_id == department_id)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Employee.first_name.ilike(search_pattern)) |
            (Employee.last_name.ilike(search_pattern)) |
            (Employee.middle_name.ilike(search_pattern))
        )
    
    employees = query.order_by(Employee.last_name, Employee.first_name).all()
    
    return [
        {
            "id": e.id,
            "first_name": e.first_name,
            "last_name": e.last_name,
            "middle_name": e.middle_name or "",
            "full_name": f"{e.last_name} {e.first_name} {e.middle_name}".strip() if e.middle_name else f"{e.last_name} {e.first_name}",
            "position": e.position or "",
            "department_id": e.department_id,
            "department_name": e.department.name if e.department else "",
            "department_code": e.department.code if e.department else "",
        }
        for e in employees
    ]


@router.get("/rooms")
async def get_available_rooms(
    search: Optional[str] = None,
    department_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    query = db.query(Room).options(
        joinedload(Room.department)
    ).filter(
        Room.is_active == True
    )

    if department_id:
        query = query.filter(Room.department_id == department_id)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Room.name.ilike(search_pattern)) |
            (Room.floor.ilike(search_pattern)) |
            (Room.building.ilike(search_pattern))
        )

    rooms = query.order_by(Room.name).all()

    return [
        {
            "id": r.id,
            "name": r.name,
            "floor": r.floor or "",
            "building": r.building or "",
            "department_id": r.department_id,
            "department_name": r.department.name if r.department else "",
            "full_name": f"{r.department.name} - {r.name}" if r.department and r.department.name else r.name,
        }
        for r in rooms
    ]


@router.get("/")
async def list_placements(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    department_id: Optional[int] = None,
    employee_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    query = db.query(Asset).filter(
        (Asset.department_code.isnot(None)) | (Asset.responsible_person.isnot(None))
    )
    
    if department_id:
        dept = db.query(Department).filter(Department.id == department_id).first()
        if dept:
            query = query.filter(Asset.department_code == dept.code)
    
    if employee_id:
        emp = db.query(Employee).filter(Employee.id == employee_id).first()
        if emp:
            emp_full = f"{emp.last_name} {emp.first_name}"
            query = query.filter(Asset.responsible_person.like(f"%{emp_full}%"))
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Asset.name.ilike(search_pattern)) | 
            (Asset.inventory_number.ilike(search_pattern)) |
            (Asset.responsible_person.ilike(search_pattern))
        )
    
    total = query.count()
    assets = query.offset(skip).limit(limit).all()
    
    result = []
    for asset in assets:
        dept_name = ""
        emp_name = ""
        location = ""
        
        if getattr(asset, 'department_code', None):
            dept = db.query(Department).filter(
                (Department.code == asset.department_code) | (Department.name == asset.department_code),
                Department.is_active == True
            ).first()
            if dept:
                dept_name = dept.name
                location = dept.location or ""
        
        if getattr(asset, 'responsible_person', None):
            emp_name = asset.responsible_person
        
        result.append(assignment_to_dict(asset, dept_name, emp_name, location))
    
    return {
        "items": result,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("/")
async def create_placement_assignment(
    data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    asset_id = data.get("asset_id")
    department_id = data.get("department_id")
    employee_id = data.get("employee_id")
    location = data.get("location", "")
    
    if not asset_id:
        raise HTTPException(status_code=400, detail="asset_id is required")
    
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    dept_code = ""
    if department_id:
        dept = db.query(Department).filter(Department.id == department_id).first()
        if not dept:
            raise HTTPException(status_code=404, detail="Department not found")
        dept_code = dept.code
    
    emp_name = ""
    if employee_id:
        emp = db.query(Employee).filter(Employee.id == employee_id).first()
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")
        emp_name = f"{emp.last_name} {emp.first_name}"
    
    if dept_code:
        asset.department_code = dept_code
    if location:
        asset.location_address = location
    if emp_name:
        asset.responsible_person = emp_name
    
    asset.updated_at = datetime.now()
    db.commit()
    db.refresh(asset)
    
    return assignment_to_dict(asset, dept_code, emp_name, location)


@router.put("/{assignment_id}")
async def update_placement_assignment(
    assignment_id: int,
    data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    asset = db.query(Asset).filter(Asset.id == assignment_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    dept_code = ""
    if "department_id" in data and data["department_id"]:
        dept = db.query(Department).filter(Department.id == data["department_id"]).first()
        if not dept:
            raise HTTPException(status_code=404, detail="Department not found")
        dept_code = dept.code
        asset.department_code = dept_code
    
    if "location" in data:
        asset.location_address = data["location"]
    
    emp_name = ""
    if "employee_id" in data and data["employee_id"]:
        emp = db.query(Employee).filter(Employee.id == data["employee_id"]).first()
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")
        emp_name = f"{emp.last_name} {emp.first_name}"
        asset.responsible_person = emp_name
    elif "employee_id" in data and not data["employee_id"]:
        asset.responsible_person = None
    
    asset.updated_at = datetime.now()
    db.commit()
    db.refresh(asset)
    
    return assignment_to_dict(asset, dept_code, emp_name, "")


@router.delete("/{assignment_id}")
async def delete_placement_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    asset = db.query(Asset).filter(Asset.id == assignment_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    asset.department_code = None
    asset.responsible_person = None
    asset.updated_at = datetime.now()
    db.commit()
    
    return {"message": "Placement assignment removed"}

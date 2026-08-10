# backend/src/presentation/http/routers/placements.py
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session, joinedload
from typing import Optional, Any
from datetime import datetime

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.department import Department, Room
from src.infrastructure.db.models.employee import Employee
from src.presentation.http.dependencies.auth import get_current_admin

router = APIRouter(prefix="/admin/placements", tags=["placements"])


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


def department_to_dict(dept):
    return {
        "id": getattr(dept, 'id', None),
        "name": safe_str(getattr(dept, 'name', None)),
        "code": safe_str(getattr(dept, 'code', None)),
        "parent_id": getattr(dept, 'parent_id', None),
        "head": safe_str(getattr(dept, 'head', None)),
        "phone": safe_str(getattr(dept, 'phone', None)),
        "email": safe_str(getattr(dept, 'email', None)),
        "location": safe_str(getattr(dept, 'location', None)),
        "is_active": getattr(dept, 'is_active', True),
        "created_at": safe_isoformat(getattr(dept, 'created_at', None)),
        "updated_at": safe_isoformat(getattr(dept, 'updated_at', None)),
    }


@router.get("/")
async def list_departments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    query = db.query(Department)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Department.name.ilike(search_pattern)) | 
            (Department.code.ilike(search_pattern))
        )
    
    if is_active is not None:
        query = query.filter(Department.is_active == is_active)
    
    total = query.count()
    departments = query.offset(skip).limit(limit).all()
    
    return {
        "items": [department_to_dict(d) for d in departments],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/options")
async def get_department_options(
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    departments = db.query(Department).filter(
        Department.is_active == True
    ).order_by(Department.name).all()
    
    return [
        {
            "id": d.id,
            "name": d.name,
            "code": d.code,
            "location": d.location or "",
            "full_name": f"{d.name} ({d.code})" if d.code else d.name,
        }
        for d in departments
    ]


@router.get("/tree")
async def get_placement_tree(
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    departments = db.query(Department).filter(
        Department.is_active == True
    ).order_by(Department.name).all()
    
    result = []
    for dept in departments:
        rooms = db.query(Room).filter(
            Room.department_id == dept.id,
            Room.is_active == True
        ).order_by(Room.name).all()
        
        dept_dict = {
            "id": dept.id,
            "name": dept.name,
            "code": dept.code,
            "parent_id": dept.parent_id,
            "head": dept.head or "",
            "phone": dept.phone or "",
            "email": dept.email or "",
            "location": dept.location or "",
            "is_active": dept.is_active,
            "rooms": [
                {
                    "id": r.id,
                    "name": r.name,
                    "floor": r.floor or "",
                    "building": r.building or "",
                }
                for r in rooms
            ],
        }
        result.append(dept_dict)
    
    return result


@router.get("/{department_id}")
async def get_department(
    department_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    
    return department_to_dict(dept)


@router.post("/")
async def create_department(
    data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    name = data.get("name")
    code = data.get("code")
    
    if not name or not code:
        raise HTTPException(status_code=400, detail="name and code are required")
    
    existing = db.query(Department).filter(Department.code == code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Department with code '{code}' already exists")
    
    dept = Department(
        organization_id=1,
        name=name,
        code=code,
        parent_id=data.get("parent_id"),
        head=data.get("head"),
        phone=data.get("phone"),
        email=data.get("email"),
        location=data.get("location"),
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    db.add(dept)
    db.commit()
    db.refresh(dept)
    
    return department_to_dict(dept)


@router.put("/{department_id}")
async def update_department(
    department_id: int,
    data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    
    if "name" in data:
        dept.name = data["name"]
    if "code" in data:
        existing = db.query(Department).filter(
            Department.code == data["code"],
            Department.id != department_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Department with code '{data['code']}' already exists")
        dept.code = data["code"]
    if "parent_id" in data:
        dept.parent_id = data["parent_id"]
    if "head" in data:
        dept.head = data["head"]
    if "phone" in data:
        dept.phone = data["phone"]
    if "email" in data:
        dept.email = data["email"]
    if "location" in data:
        dept.location = data["location"]
    if "is_active" in data:
        dept.is_active = data["is_active"]
    
    dept.updated_at = datetime.now()
    db.commit()
    db.refresh(dept)
    
    return department_to_dict(dept)


@router.delete("/{department_id}")
async def delete_department(
    department_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    
    db.delete(dept)
    db.commit()
    
    return {"message": "Department deleted successfully"}


@router.get("/{department_id}/employees")
async def get_department_employees(
    department_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    
    employees = db.query(Employee).filter(
        Employee.department_id == department_id,
        Employee.is_active == True
    ).order_by(Employee.last_name, Employee.first_name).all()
    
    return [
        {
            "id": e.id,
            "first_name": safe_str(getattr(e, 'first_name', None)),
            "last_name": safe_str(getattr(e, 'last_name', None)),
            "middle_name": safe_str(getattr(e, 'middle_name', None)),
            "full_name": f"{getattr(e, 'last_name', '')} {getattr(e, 'first_name', '')} {getattr(e, 'middle_name', '')}".strip(),
            "position": safe_str(getattr(e, 'position', None)),
            "phone": safe_str(getattr(e, 'phone', None)),
            "email": safe_str(getattr(e, 'email', None)),
            "employee_number": safe_str(getattr(e, 'employee_number', None)),
            "department_id": getattr(e, 'department_id', None),
            "department_name": dept.name,
        }
        for e in employees
    ]


def room_to_dict(room):
    return {
        "id": getattr(room, 'id', None),
        "department_id": getattr(room, 'department_id', None),
        "name": safe_str(getattr(room, 'name', None)),
        "floor": safe_str(getattr(room, 'floor', None)),
        "building": safe_str(getattr(room, 'building', None)),
        "is_active": getattr(room, 'is_active', True),
        "created_at": safe_isoformat(getattr(room, 'created_at', None)),
        "updated_at": safe_isoformat(getattr(room, 'updated_at', None)),
    }


@router.get("/{department_id}/rooms")
async def get_department_rooms(
    department_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    
    rooms = db.query(Room).filter(
        Room.department_id == department_id,
        Room.is_active == True
    ).order_by(Room.name).all()
    
    return [room_to_dict(r) for r in rooms]


@router.post("/{department_id}/rooms")
async def create_room(
    department_id: int,
    data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    
    name = data.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Название кабинета обязательно")
    
    room = Room(
        department_id=department_id,
        name=name,
        floor=data.get("floor"),
        building=data.get("building"),
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    db.add(room)
    db.commit()
    db.refresh(room)
    
    return room_to_dict(room)


@router.put("/rooms/{room_id}")
async def update_room(
    room_id: int,
    data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Кабинет не найден")
    
    if "name" in data:
        room.name = data["name"]
    if "floor" in data:
        room.floor = data["floor"]
    if "building" in data:
        room.building = data["building"]
    if "is_active" in data:
        room.is_active = data["is_active"]
    if "department_id" in data:
        dept = db.query(Department).filter(Department.id == data["department_id"]).first()
        if not dept:
            raise HTTPException(status_code=404, detail="Подразделение не найдено")
        room.department_id = data["department_id"]
    
    room.updated_at = datetime.now()
    db.commit()
    db.refresh(room)
    
    return room_to_dict(room)


@router.delete("/rooms/{room_id}")
async def delete_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Кабинет не найден")
    
    db.delete(room)
    db.commit()
    
    return {"message": "Кабинет удален"}


@router.put("/rooms/{room_id}/move")
async def move_room(
    room_id: int,
    data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    """
    Переместить кабинет в другое подразделение.
    Все привязанные активы автоматически сохраняют связь с кабинетом.
    
    При изменении room.department_id:
    - кабинет переходит в новое подразделение
    - location_address активов, привязанных к этому кабинету, обновляется
    - department_code активов обновляется на новое подразделение
    """
    from src.infrastructure.db.models.asset import Asset
    
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Кабинет не найден")
    
    new_department_id = data.get("department_id")
    if new_department_id is None:
        raise HTTPException(status_code=400, detail="department_id обязателен")
    
    new_dept = db.query(Department).filter(
        Department.id == new_department_id,
        Department.is_active == True
    ).first()
    if not new_dept:
        raise HTTPException(status_code=404, detail="Подразделение не найдено или неактивно")
    
    old_department_id = room.department_id
    
    # Если кабинет уже в этом подразделении — ничего не делаем
    if old_department_id == new_department_id:
        return {
            "message": f"Кабинет '{room.name}' уже находится в '{new_dept.name}'",
            "room": room_to_dict(room),
        }
    
    old_dept = db.query(Department).filter(Department.id == old_department_id).first()
    
    # Перемещаем кабинет
    room.department_id = new_department_id
    room.updated_at = datetime.now()
    
    # Обновляем location_address для всех активов, привязанных к этому кабинету
    assets_in_room = db.query(Asset).filter(
        Asset.room_id == room_id
    ).all()
    
    # Формируем новый location_address: "ИмяКабинета (КодПодразделения)"
    new_location = f"{room.name} ({new_dept.code})"
    
    updated_assets = 0
    for asset in assets_in_room:
        asset.location_address = new_location
        # Обновляем department_code если он совпадает со старым подразделением
        if old_dept and (asset.department_code == old_dept.code or asset.department_code == old_dept.name):
            asset.department_code = new_dept.code
        updated_assets += 1
    
    db.commit()
    
    return {
        "message": f"Кабинет '{room.name}' перемещен из '{old_dept.name}' в '{new_dept.name}'",
        "room": room_to_dict(room),
        "assets_moved": updated_assets,
        "new_location": new_location,
    }

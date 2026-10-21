# backend/src/presentation/http/routers/placements.py
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import FileResponse, JSONResponse
from fastapi.background import BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from typing import Optional, Any
from datetime import datetime
import os

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.department import Department, Room
from src.infrastructure.db.models.employee import Employee
from src.presentation.http.dependencies.auth import get_current_admin

router = APIRouter(prefix="/admin/placements", tags=["placements"])


def _save_print_record(
    room_id: int,
    room_name: str,
    department_id: Optional[int],
    department_name: str,
    employee_id: Optional[int],
    employee_name: str,
    employee_position: str,
    asset_count: int,
    file_path: str,
    user_id: int,
):
    """Background task для сохранения записи о распечатанной описи"""
    from src.infrastructure.db.session import SessionLocal
    from src.infrastructure.db.models.room_inventory_print import RoomInventoryPrint
    
    db = SessionLocal()
    try:
        print_record = RoomInventoryPrint(
            room_id=room_id,
            room_name=room_name,
            department_id=department_id,
            department_name=department_name,
            employee_id=employee_id,
            employee_name=employee_name,
            employee_position=employee_position,
            asset_count=asset_count,
            file_path=file_path,
            signed=False,
            created_by_user_id=user_id,
            created_at=datetime.now(),
        )
        db.add(print_record)
        db.commit()
    except Exception as e:
        print(f"❌ Error saving print record: {e}")
        db.rollback()
    finally:
        db.close()


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


@router.get("/{department_id:int}")
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


@router.put("/{department_id:int}")
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


@router.delete("/{department_id:int}")
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
    
    # Формируем новый location_address: "ИмяКабинета (НазваниеПодразделения)"
    new_location = f"{room.name} ({new_dept.name})"
    
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


# ======================================================================
# ОПИСЬ ПОМЕЩЕНИЯ
# ======================================================================

REPORTS_DIR = "uploads/reports"
os.makedirs(REPORTS_DIR, exist_ok=True)


@router.get("/{department_id}/rooms-with-assets")
async def get_rooms_with_assets(
    department_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    """
    Получить список кабинетов подразделения с количеством активов.
    """
    from src.infrastructure.db.models.asset import Asset

    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Подразделение не найдено")

    rooms = db.query(Room).filter(
        Room.department_id == department_id,
        Room.is_active == True
    ).order_by(Room.name).all()

    result = []
    for room in rooms:
        dept = db.query(Department).filter(Department.id == room.department_id).first()
        dept_code = dept.code if dept else ""
        location_pattern = f"{room.name} ({dept_code})" if dept_code else room.name

        # Считаем по room_id ИЛИ по location_address
        assets_direct = db.query(Asset).filter(
            Asset.room_id == room.id,
            Asset.is_active == True
        ).all()

        assets_location = db.query(Asset).filter(
            Asset.location_address.like(f"%{room.name}%"),
            Asset.is_active == True
        ).all()

        # Объединяем, убираем дубликаты
        seen_ids = set()
        for a in assets_direct + assets_location:
            seen_ids.add(a.id)

        result.append({
            "id": room.id,
            "name": room.name,
            "floor": room.floor or "",
            "building": room.building or "",
            "asset_count": len(seen_ids),
        })

    return result


@router.get("/{room_id}/assets")
async def get_room_assets(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    """Получить активы кабинета (для формирования актов передачи).
    Используется та же логика отбора, что и при печати описи:
    прямая привязка room_id ИЛИ строковая привязка location_address."""
    from src.infrastructure.db.models.asset import Asset

    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Кабинет не найден")

    assets_direct = db.query(Asset).filter(
        Asset.room_id == room_id,
        Asset.is_active == True
    ).order_by(Asset.inventory_number).all()

    assets_location = db.query(Asset).filter(
        Asset.location_address.like(f"%{room.name}%"),
        Asset.is_active == True
    ).order_by(Asset.inventory_number).all()

    seen_ids = set()
    assets = []
    for a in assets_direct + assets_location:
        if a.id not in seen_ids:
            seen_ids.add(a.id)
            assets.append(a)

    from src.infrastructure.db.models.employee import Employee as EmpModel

    result = []
    for asset in assets:
        emp_name = None
        if asset.employee_id:
            emp = db.query(EmpModel).filter(EmpModel.id == asset.employee_id).first()
            if emp:
                emp_name = f"{emp.last_name} {emp.first_name} {emp.middle_name or ''}".strip()
        result.append({
            "id": asset.id,
            "name": asset.name or "Без названия",
            "inventory_number": asset.inventory_number or "",
            "quantity": asset.quantity or 1,
            "model": asset.model or "",
            "serial_number": asset.serial_number or "",
            "asset_type": asset.asset_type or "",
            "status": asset.status or "",
            "employee_id": asset.employee_id,
            "employee_name": emp_name,
            "responsible_person": asset.responsible_person or "",
            "location_address": asset.location_address or "",
            "room_id": asset.room_id,
        })

    return JSONResponse(content=result)


@router.post("/{room_id}/print/inventory")
async def print_room_inventory(
    room_id: int,
    data: dict = Body(default={"employee_id": None}),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    """
    Сгенерировать опись имущества для указанного кабинета.
    Возвращает Excel-файл для скачивания.
    
    Body: {"employee_id": int | null} — сотрудник, подписывающий опись
    """
    from src.infrastructure.db.models.asset import Asset
    from src.infrastructure.db.models.department import Department
    from src.infrastructure.db.models.employee import Employee
    from src.infrastructure.db.models.room_inventory_print import RoomInventoryPrint
    from src.infrastructure.reports.room_inventory_report import RoomInventoryReportGenerator

    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Кабинет не найден")

    dept = db.query(Department).filter(Department.id == room.department_id).first()
    department_name = dept.name if dept else ""

    # Формируем location_address как в move_room: "ИмяКабинета (НазваниеПодразделения)"
    location_pattern = f"{room.name} ({dept.name})" if dept else room.name

    # Ищем по room_id (прямая привязка) ИЛИ по location_address (строковая привязка)
    assets_direct = db.query(Asset).filter(
        Asset.room_id == room_id,
        Asset.is_active == True
    ).order_by(Asset.inventory_number).all()

    assets_location = db.query(Asset).filter(
        Asset.location_address.like(f"%{room.name}%"),
        Asset.is_active == True
    ).order_by(Asset.inventory_number).all()

    # Объединяем, убираем дубликаты по id
    seen_ids = set()
    assets = []
    for a in assets_direct + assets_location:
        if a.id not in seen_ids:
            seen_ids.add(a.id)
            assets.append(a)

    assets_data = []
    for asset in assets:
        assets_data.append({
            "name": asset.name or "Без названия",
            "inventory_number": asset.inventory_number or "",
            "quantity": asset.quantity or 1,
            "model": asset.model or "",
            "serial_number": asset.serial_number or "",
        })

    # Данные сотрудника (подписанта)
    employee_id = data.get("employee_id")
    senior_inspector = ''
    position = ''
    if employee_id:
        emp = db.query(Employee).filter(
            Employee.id == employee_id,
            Employee.is_active == True
        ).first()
        if emp:
            position = emp.position or ''
            # Формируем "Фамилия И.О."
            initials = ''
            if emp.first_name:
                initials += emp.first_name[0].upper() + '.'
            if emp.middle_name:
                initials += emp.middle_name[0].upper() + '.'
            senior_inspector = f"{emp.last_name} {initials}".strip()

    generator = RoomInventoryReportGenerator()
    excel_bytes = generator.generate(
        room_name=room.name,
        department_name=department_name,
        assets=assets_data,
        senior_inspector=senior_inspector,
        position=position,
    )

    filename = f"опись_{room.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = os.path.join(REPORTS_DIR, filename)
    with open(filepath, 'wb') as f:
        f.write(excel_bytes)

    # Сохраняем запись в БД ДО отправки файла
    print_record = RoomInventoryPrint(
        room_id=room.id,
        room_name=room.name,
        department_id=room.department_id,
        department_name=department_name,
        employee_id=employee_id,
        employee_name=senior_inspector,
        employee_position=position,
        asset_count=len(assets_data),
        file_path=filepath,
        signed=False,
        created_by_user_id=current_user.id,
        created_at=datetime.now(),
    )
    db.add(print_record)
    db.commit()
    db.refresh(print_record)

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.get("/inventory-prints")
async def list_room_inventory_prints(
    room_id: Optional[int] = Query(None, description="Фильтр по кабинету"),
    signed: Optional[bool] = Query(None, description="Фильтр по статусу подписания"),
    archived: Optional[bool] = Query(None, description="Фильтр по статусу архивации (по умолчанию — только неархивированные)"),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    """Получить список распечатанных описей"""
    from src.infrastructure.db.models.room_inventory_print import RoomInventoryPrint
    from src.infrastructure.db.models.employee import Employee
    
    query = db.query(RoomInventoryPrint).options(
        joinedload(RoomInventoryPrint.employee),
    )
    
    if room_id:
        query = query.filter(RoomInventoryPrint.room_id == room_id)
    if signed is not None:
        query = query.filter(RoomInventoryPrint.signed == signed)
    # По умолчанию скрываем архивированные описи
    if archived is None:
        query = query.filter(RoomInventoryPrint.is_archived == False)
    else:
        query = query.filter(RoomInventoryPrint.is_archived == archived)
    
    prints = query.order_by(RoomInventoryPrint.created_at.desc()).all()
    
    result = []
    for p in prints:
        employee_data = None
        if p.employee_id:
            emp = db.query(Employee).filter(Employee.id == p.employee_id).first()
            if emp:
                employee_data = {
                    "id": emp.id,
                    "name": f"{emp.last_name} {emp.first_name[0].upper()}.{''.join([emp.middle_name[0].upper() + '.' if emp.middle_name else ''])}".strip(),
                    "position": emp.position or '',
                }
        
        result.append({
            "id": p.id,
            "room_id": p.room_id,
            "room_name": p.room_name,
            "department_name": p.department_name,
            "employee_id": p.employee_id,
            "employee_name": p.employee_name,
            "employee_position": p.employee_position,
            "employee": employee_data,
            "asset_count": p.asset_count,
            "file_path": p.file_path,
            "signed": p.signed,
            "signed_at": p.signed_at.isoformat() if p.signed_at else None,
            "signed_by": p.signed_by_user.full_name if p.signed_by_user else None,
            "created_by": p.created_by_user.full_name if p.created_by_user else None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "is_archived": p.is_archived,
            "archived_at": p.archived_at.isoformat() if p.archived_at else None,
        })
    
    return JSONResponse(content=result)


@router.post("/inventory-prints/{print_id}/confirm")
async def confirm_inventory_print(
    print_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    """
    Подтвердить подписание описи.
    При подтверждении активам в кабинете проставляется employee_id подписанта.
    """
    from src.infrastructure.db.models.room_inventory_print import RoomInventoryPrint
    from src.infrastructure.db.models.asset import Asset
    from src.infrastructure.db.models.employee import Employee
    
    print_record = db.query(RoomInventoryPrint).filter(
        RoomInventoryPrint.id == print_id
    ).first()
    
    if not print_record:
        raise HTTPException(status_code=404, detail="Запись описи не найдена")
    
    if print_record.signed:
        raise HTTPException(status_code=400, detail="Опись уже подписана")
    
    if print_record.is_archived:
        raise HTTPException(status_code=400, detail="Нельзя подтвердить архивированную опись")
    
    # Получаем сотрудника-подписанта
    employee = None
    if print_record.employee_id:
        employee = db.query(Employee).filter(Employee.id == print_record.employee_id).first()
    
    # Проставляем employee_id для всех активов в кабинете.
    # Та же логика отбора, что и при генерации описи: активы, привязанные
    # напрямую (room_id), ИЛИ строковой привязкой (location_address).
    if employee:
        from src.infrastructure.db.models.asset_transfer_history import AssetTransferHistory

        assets = db.query(Asset).filter(
            or_(
                Asset.room_id == print_record.room_id,
                Asset.location_address.like(f"%{print_record.room_name}%"),
            ),
            Asset.is_active == True
        ).all()
        
        full_name = f"{employee.last_name} {employee.first_name} {employee.middle_name or ''}".strip()
        source_ref = f"Опись кабинета {print_record.room_name or ''}".strip()
        
        for asset in assets:
            prev_emp_id = asset.employee_id
            prev_emp_name = None
            if prev_emp_id:
                prev = db.query(Employee).filter(Employee.id == prev_emp_id).first()
                if prev:
                    prev_emp_name = f"{prev.last_name} {prev.first_name} {prev.middle_name or ''}".strip()

            asset.employee_id = employee.id
            asset.responsible_person = full_name

            # История передачи актива
            history = AssetTransferHistory(
                asset_id=asset.id,
                prev_employee_id=prev_emp_id,
                prev_employee_name=prev_emp_name,
                new_employee_id=employee.id,
                new_employee_name=full_name,
                source="inventory_print",
                source_id=print_record.id,
                source_ref=source_ref,
                transfer_date=datetime.now(),
                created_by_user_id=current_user.id,
                created_at=datetime.now(),
            )
            db.add(history)
    
    # Отмечаем опись как подписанную
    print_record.signed = True
    print_record.signed_at = datetime.now()
    print_record.signed_by_user_id = current_user.id
    
    db.commit()
    
    assets_updated = len(db.query(Asset).filter(
        or_(
            Asset.room_id == print_record.room_id,
            Asset.location_address.like(f"%{print_record.room_name}%"),
        ),
        Asset.is_active == True
    ).all()) if employee else 0
    
    return JSONResponse(content={
        "message": "Опись подтверждена, активам проставлен сотрудник",
        "print_id": print_record.id,
        "assets_updated": assets_updated,
    })


@router.post("/inventory-prints/{print_id}/archive")
async def archive_inventory_print(
    print_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    """
    Архивировать опись (отметить как не подписанную).
    Активам ничего не присваивается.
    """
    from src.infrastructure.db.models.room_inventory_print import RoomInventoryPrint
    
    print_record = db.query(RoomInventoryPrint).filter(
        RoomInventoryPrint.id == print_id
    ).first()
    
    if not print_record:
        raise HTTPException(status_code=404, detail="Запись описи не найдена")
    
    if print_record.signed:
        raise HTTPException(status_code=400, detail="Нельзя архивировать подписанную опись")
    
    if print_record.is_archived:
        raise HTTPException(status_code=400, detail="Опись уже архивирована")
    
    # Отмечаем опись как архивированную — она больше не появится в списке
    print_record.is_archived = True
    print_record.archived_at = datetime.now()
    print_record.signed = False
    db.commit()
    
    return JSONResponse(content={
        "message": "Опись архивирована",
        "print_id": print_record.id,
    })


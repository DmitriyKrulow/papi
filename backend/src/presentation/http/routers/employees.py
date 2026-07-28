# backend/src/presentation/http/routers/employees.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, Any
from datetime import datetime, date

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.employee import Employee
from src.infrastructure.db.models.department import Department
from src.presentation.http.dependencies.auth import get_current_admin

router = APIRouter(prefix="/admin/employees", tags=["employees"])


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


def employee_to_dict(emp):
    dept = getattr(emp, 'department', None)
    dept_name = dept.name if dept else None
    dept_code = dept.code if dept else None
    
    user = getattr(emp, 'user', None)
    user_id = user.id if user else None
    username = user.username if user else None
    
    full_name = f"{emp.last_name} {emp.first_name} {emp.middle_name}".strip() if emp.middle_name else f"{emp.last_name} {emp.first_name}".strip()
    
    return {
        "id": getattr(emp, 'id', None),
        "first_name": safe_str(getattr(emp, 'first_name', None)),
        "last_name": safe_str(getattr(emp, 'last_name', None)),
        "middle_name": safe_str(getattr(emp, 'middle_name', None)),
        "full_name": full_name,
        "position": safe_str(getattr(emp, 'position', None)),
        "position_code": safe_str(getattr(emp, 'position_code', None)),
        "phone": safe_str(getattr(emp, 'phone', None)),
        "email": safe_str(getattr(emp, 'email', None)),
        "employee_number": safe_str(getattr(emp, 'employee_number', None)),
        "department_id": getattr(emp, 'department_id', None),
        "department_name": dept_name,
        "department_code": dept_code,
        "user_id": user_id,
        "username": username,
        "hire_date": safe_isoformat(getattr(emp, 'hire_date', None)),
        "termination_date": safe_isoformat(getattr(emp, 'termination_date', None)),
        "is_active": getattr(emp, 'is_active', True),
        "created_at": safe_isoformat(getattr(emp, 'created_at', None)),
        "updated_at": safe_isoformat(getattr(emp, 'updated_at', None)),
    }


@router.get("/")
async def list_employees(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    department_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    query = db.query(Employee).options(
        joinedload(Employee.department),
        joinedload(Employee.user)
    )
    
    if search:
        query = query.filter(
            (Employee.first_name.contains(search)) |
            (Employee.last_name.contains(search)) |
            (Employee.middle_name.contains(search)) |
            (Employee.position.contains(search)) |
            (Employee.phone.contains(search))
        )
    
    if department_id:
        query = query.filter(Employee.department_id == department_id)
    
    if is_active is not None:
        query = query.filter(Employee.is_active == is_active)
    
    total = query.count()
    employees = query.offset(skip).limit(limit).all()
    
    return {
        "items": [employee_to_dict(e) for e in employees],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/options")
async def get_employee_options(
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    employees = db.query(Employee).filter(
        Employee.is_active == True
    ).order_by(Employee.last_name, Employee.first_name).all()
    
    return [
        {
            "id": e.id,
            "full_name": f"{e.last_name} {e.first_name} {e.middle_name}".strip() if e.middle_name else f"{e.last_name} {e.first_name}".strip(),
            "position": e.position or "",
            "department_name": e.department.name if e.department else "",
            "department_code": e.department.code if e.department else "",
        }
        for e in employees
    ]


@router.get("/{employee_id}")
async def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    emp = db.query(Employee).options(
        joinedload(Employee.department),
        joinedload(Employee.user)
    ).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return employee_to_dict(emp)


@router.post("/")
async def create_employee(
    data: dict,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    department_id = data.get("department_id")
    user_id = data.get("user_id")
    
    if not department_id:
        raise HTTPException(status_code=400, detail="department_id is required")
    
    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    
    if user_id:
        existing = db.query(Employee).filter(
            Employee.user_id == user_id,
            Employee.is_active == True
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="User is already assigned as an employee")
    
    emp = Employee(
        department_id=department_id,
        user_id=user_id,
        first_name=data.get("first_name", ""),
        last_name=data.get("last_name", ""),
        middle_name=data.get("middle_name"),
        phone=data.get("phone"),
        email=data.get("email"),
        position=data.get("position"),
        position_code=data.get("position_code"),
        employee_number=data.get("employee_number"),
        hire_date=None,
        termination_date=None,
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    hire_date = data.get("hire_date")
    if hire_date:
        try:
            emp.hire_date = datetime.strptime(hire_date, "%Y-%m-%d").date()
        except:
            emp.hire_date = date.fromisoformat(hire_date)
    
    db.add(emp)
    db.commit()
    db.refresh(emp)
    
    return employee_to_dict(emp)


@router.put("/{employee_id}")
async def update_employee(
    employee_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    emp = db.query(Employee).options(
        joinedload(Employee.department),
        joinedload(Employee.user)
    ).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    if "department_id" in data:
        dept = db.query(Department).filter(Department.id == data["department_id"]).first()
        if not dept:
            raise HTTPException(status_code=404, detail="Department not found")
        emp.department_id = data["department_id"]
    
    if "first_name" in data:
        emp.first_name = data["first_name"]
    if "last_name" in data:
        emp.last_name = data["last_name"]
    if "middle_name" in data:
        emp.middle_name = data["middle_name"]
    if "phone" in data:
        emp.phone = data["phone"]
    if "email" in data:
        emp.email = data["email"]
    if "position" in data:
        emp.position = data["position"]
    if "position_code" in data:
        emp.position_code = data["position_code"]
    if "employee_number" in data:
        emp.employee_number = data["employee_number"]
    if "user_id" in data:
        emp.user_id = data["user_id"]
    if "is_active" in data:
        emp.is_active = data["is_active"]
    
    if "hire_date" in data:
        hire_date = data["hire_date"]
        if hire_date:
            try:
                emp.hire_date = datetime.strptime(hire_date, "%Y-%m-%d").date()
            except:
                emp.hire_date = date.fromisoformat(hire_date)
        else:
            emp.hire_date = None
    
    if "termination_date" in data:
        term_date = data["termination_date"]
        if term_date:
            try:
                emp.termination_date = datetime.strptime(term_date, "%Y-%m-%d").date()
            except:
                emp.termination_date = date.fromisoformat(term_date)
        else:
            emp.termination_date = None
    
    emp.updated_at = datetime.now()
    db.commit()
    db.refresh(emp)
    
    return employee_to_dict(emp)


@router.delete("/{employee_id}")
async def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    db.delete(emp)
    db.commit()
    
    return {"message": "Employee deleted successfully"}

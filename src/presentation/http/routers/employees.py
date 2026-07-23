from typing import List

from fastapi import APIRouter, HTTPException, Depends
from src.presentation.schemas.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
)
from src.infrastructure.db.unit_of_work import UnitOfWork

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.get("/", response_model=List[EmployeeResponse])
def list_employees(uow: UnitOfWork = Depends()):
    employees = uow.employee_repository.list_all()
    return employees


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(employee_id: int, uow: UnitOfWork = Depends()):
    employee = uow.employee_repository.get_by_id(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@router.get("/user/{user_id}", response_model=EmployeeResponse)
def get_employee_by_user(user_id: int, uow: UnitOfWork = Depends()):
    employee = uow.employee_repository.get_by_user_id(user_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@router.post("/", response_model=EmployeeResponse, status_code=201)
def create_employee(employee: EmployeeCreate, uow: UnitOfWork = Depends()):
    try:
        uow.employee_repository.save(employee)
        uow.commit()
        return uow.employee_repository.get_by_id(employee.id)
    except Exception as e:
        uow.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: int, employee: EmployeeUpdate, uow: UnitOfWork = Depends()
):
    existing_employee = uow.employee_repository.get_by_id(employee_id)
    if not existing_employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    try:
        uow.employee_repository.save(employee)
        uow.commit()
        return uow.employee_repository.get_by_id(employee_id)
    except Exception as e:
        uow.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{employee_id}", status_code=204)
def delete_employee(employee_id: int, uow: UnitOfWork = Depends()):
    existing_employee = uow.employee_repository.get_by_id(employee_id)
    if not existing_employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    try:
        uow.employee_repository.delete(employee_id)
        uow.commit()
    except Exception as e:
        uow.rollback()
        raise HTTPException(status_code=400, detail=str(e))

from typing import List

from fastapi import APIRouter, HTTPException, Depends
from src.presentation.schemas.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
)
from src.infrastructure.db.unit_of_work import UnitOfWork

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.get("/", response_model=List[DepartmentResponse])
def list_departments(uow: UnitOfWork = Depends()):
    departments = uow.department_repository.list_all()
    return departments


@router.get("/{department_id}", response_model=DepartmentResponse)
def get_department(department_id: int, uow: UnitOfWork = Depends()):
    department = uow.department_repository.get_by_id(department_id)
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    return department


@router.get("/code/{department_code}", response_model=DepartmentResponse)
def get_department_by_code(department_code: str, uow: UnitOfWork = Depends()):
    department = uow.department_repository.get_by_code(department_code)
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    return department


@router.post("/", response_model=DepartmentResponse, status_code=201)
def create_department(department: DepartmentCreate, uow: UnitOfWork = Depends()):
    try:
        uow.department_repository.save(department)
        uow.commit()
        return uow.department_repository.get_by_id(department.id)
    except Exception as e:
        uow.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{department_id}", response_model=DepartmentResponse)
def update_department(
    department_id: int, department: DepartmentUpdate, uow: UnitOfWork = Depends()
):
    existing_department = uow.department_repository.get_by_id(department_id)
    if not existing_department:
        raise HTTPException(status_code=404, detail="Department not found")
    try:
        uow.department_repository.save(department)
        uow.commit()
        return uow.department_repository.get_by_id(department_id)
    except Exception as e:
        uow.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{department_id}", status_code=204)
def delete_department(department_id: int, uow: UnitOfWork = Depends()):
    existing_department = uow.department_repository.get_by_id(department_id)
    if not existing_department:
        raise HTTPException(status_code=404, detail="Department not found")
    try:
        uow.department_repository.delete(department_id)
        uow.commit()
    except Exception as e:
        uow.rollback()
        raise HTTPException(status_code=400, detail=str(e))

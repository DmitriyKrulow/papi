from typing import List

from fastapi import APIRouter, HTTPException, Depends
from src.presentation.schemas.repair import (
    RepairCreate,
    RepairUpdate,
    RepairResponse,
    RepairListResponse,
    RepairStatusUpdate,
    RepairPriorityUpdate,
)
from src.infrastructure.db.unit_of_work import UnitOfWork

router = APIRouter(prefix="/repairs", tags=["Repairs"])


@router.get("/", response_model=RepairListResponse)
def list_repairs(uow: UnitOfWork = Depends()):
    repairs = uow.repair_repository.list_all()
    return {"total": len(repairs), "items": repairs}


@router.get("/{repair_id}", response_model=RepairResponse)
def get_repair(repair_id: int, uow: UnitOfWork = Depends()):
    repair = uow.repair_repository.get_by_id(repair_id)
    if not repair:
        raise HTTPException(status_code=404, detail="Repair not found")
    return repair


@router.post("/", response_model=RepairResponse, status_code=201)
def create_repair(repair: RepairCreate, uow: UnitOfWork = Depends()):
    try:
        uow.repair_repository.save(repair)
        uow.commit()
        return uow.repair_repository.get_by_id(repair.id)
    except Exception as e:
        uow.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{repair_id}", response_model=RepairResponse)
def update_repair(repair_id: int, repair: RepairUpdate, uow: UnitOfWork = Depends()):
    existing_repair = uow.repair_repository.get_by_id(repair_id)
    if not existing_repair:
        raise HTTPException(status_code=404, detail="Repair not found")
    try:
        uow.repair_repository.save(repair)
        uow.commit()
        return uow.repair_repository.get_by_id(repair_id)
    except Exception as e:
        uow.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{repair_id}/status", response_model=RepairResponse)
def update_repair_status(
    repair_id: int, status_update: RepairStatusUpdate, uow: UnitOfWork = Depends()
):
    repair = uow.repair_repository.get_by_id(repair_id)
    if not repair:
        raise HTTPException(status_code=404, detail="Repair not found")
    try:
        repair.status = status_update.status
        repair.updated_by = status_update.updated_by
        uow.repair_repository.save(repair)
        uow.commit()
        return repair
    except Exception as e:
        uow.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{repair_id}/priority", response_model=RepairResponse)
def update_repair_priority(
    repair_id: int, priority_update: RepairPriorityUpdate, uow: UnitOfWork = Depends()
):
    repair = uow.repair_repository.get_by_id(repair_id)
    if not repair:
        raise HTTPException(status_code=404, detail="Repair not found")
    try:
        repair.priority = priority_update.priority
        repair.updated_by = priority_update.updated_by
        uow.repair_repository.save(repair)
        uow.commit()
        return repair
    except Exception as e:
        uow.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{repair_id}", status_code=204)
def delete_repair(repair_id: int, uow: UnitOfWork = Depends()):
    existing_repair = uow.repair_repository.get_by_id(repair_id)
    if not existing_repair:
        raise HTTPException(status_code=404, detail="Repair not found")
    try:
        uow.repair_repository.delete(repair_id)
        uow.commit()
    except Exception as e:
        uow.rollback()
        raise HTTPException(status_code=400, detail=str(e))

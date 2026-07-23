from typing import List

from fastapi import APIRouter, HTTPException, Depends
from src.presentation.schemas.maintenance import MaintenanceCreate, MaintenanceResponse
from src.infrastructure.db.unit_of_work import UnitOfWork

router = APIRouter(prefix="/maintenance", tags=["Maintenance"])


@router.get("/", response_model=List[MaintenanceResponse])
def list_maintenance(uow: UnitOfWork = Depends()):
    maintenance = uow.maintenance_repository.list_all()
    return maintenance


@router.get("/{maintenance_id}", response_model=MaintenanceResponse)
def get_maintenance(maintenance_id: int, uow: UnitOfWork = Depends()):
    maintenance = uow.maintenance_repository.get_by_id(maintenance_id)
    if not maintenance:
        raise HTTPException(status_code=404, detail="Maintenance not found")
    return maintenance


@router.get("/asset/{asset_id}", response_model=List[MaintenanceResponse])
def get_maintenance_by_asset(asset_id: int, uow: UnitOfWork = Depends()):
    maintenance = uow.maintenance_repository.list_by_asset(asset_id)
    return maintenance


@router.post("/", response_model=MaintenanceResponse, status_code=201)
def create_maintenance(maintenance: MaintenanceCreate, uow: UnitOfWork = Depends()):
    try:
        uow.maintenance_repository.save(maintenance)
        uow.commit()
        return uow.maintenance_repository.get_by_id(maintenance.id)
    except Exception as e:
        uow.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{maintenance_id}", status_code=204)
def delete_maintenance(maintenance_id: int, uow: UnitOfWork = Depends()):
    existing_maintenance = uow.maintenance_repository.get_by_id(maintenance_id)
    if not existing_maintenance:
        raise HTTPException(status_code=404, detail="Maintenance not found")
    try:
        uow.maintenance_repository.delete(maintenance_id)
        uow.commit()
    except Exception as e:
        uow.rollback()
        raise HTTPException(status_code=400, detail=str(e))

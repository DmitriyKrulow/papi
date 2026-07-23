from typing import List

from fastapi import APIRouter, HTTPException, Depends
from src.presentation.schemas.inventory import InventoryCreate, InventoryResponse
from src.infrastructure.db.unit_of_work import UnitOfWork

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("/", response_model=List[InventoryResponse])
def list_inventory(uow: UnitOfWork = Depends()):
    inventory = uow.inventory_repository.list_all()
    return inventory


@router.get("/{inventory_id}", response_model=InventoryResponse)
def get_inventory(inventory_id: int, uow: UnitOfWork = Depends()):
    inventory = uow.inventory_repository.get_by_id(inventory_id)
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")
    return inventory


@router.get("/department/{department_id}", response_model=List[InventoryResponse])
def get_inventory_by_department(department_id: int, uow: UnitOfWork = Depends()):
    inventory = uow.inventory_repository.list_by_department(department_id)
    return inventory


@router.post("/", response_model=InventoryResponse, status_code=201)
def create_inventory(inventory: InventoryCreate, uow: UnitOfWork = Depends()):
    try:
        uow.inventory_repository.save(inventory)
        uow.commit()
        return uow.inventory_repository.get_by_id(inventory.id)
    except Exception as e:
        uow.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{inventory_id}", status_code=204)
def delete_inventory(inventory_id: int, uow: UnitOfWork = Depends()):
    existing_inventory = uow.inventory_repository.get_by_id(inventory_id)
    if not existing_inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")
    try:
        uow.inventory_repository.delete(inventory_id)
        uow.commit()
    except Exception as e:
        uow.rollback()
        raise HTTPException(status_code=400, detail=str(e))

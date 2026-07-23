from typing import List

from fastapi import APIRouter, HTTPException, Depends
from src.presentation.schemas.movement import MovementCreate, MovementResponse
from src.infrastructure.db.unit_of_work import UnitOfWork

router = APIRouter(prefix="/movements", tags=["Movements"])


@router.get("/", response_model=List[MovementResponse])
def list_movements(uow: UnitOfWork = Depends()):
    movements = uow.movement_repository.list_all()
    return movements


@router.get("/{movement_id}", response_model=MovementResponse)
def get_movement(movement_id: int, uow: UnitOfWork = Depends()):
    movement = uow.movement_repository.get_by_id(movement_id)
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")
    return movement


@router.post("/", response_model=MovementResponse, status_code=201)
def create_movement(movement: MovementCreate, uow: UnitOfWork = Depends()):
    try:
        uow.movement_repository.save(movement)
        uow.commit()
        return uow.movement_repository.get_by_id(movement.id)
    except Exception as e:
        uow.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{movement_id}", status_code=204)
def delete_movement(movement_id: int, uow: UnitOfWork = Depends()):
    existing_movement = uow.movement_repository.get_by_id(movement_id)
    if not existing_movement:
        raise HTTPException(status_code=404, detail="Movement not found")
    try:
        uow.movement_repository.delete(movement_id)
        uow.commit()
    except Exception as e:
        uow.rollback()
        raise HTTPException(status_code=400, detail=str(e))

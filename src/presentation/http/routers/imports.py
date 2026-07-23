from typing import List

from fastapi import APIRouter, HTTPException, Depends
from src.presentation.schemas.import_job import ImportJobCreate, ImportJobResponse
from src.infrastructure.db.unit_of_work import UnitOfWork

router = APIRouter(prefix="/imports", tags=["Imports"])


@router.get("/", response_model=List[ImportJobResponse])
def list_imports(uow: UnitOfWork = Depends()):
    imports = uow.import_repository.list_all()
    return imports


@router.get("/{import_id}", response_model=ImportJobResponse)
def get_import(import_id: int, uow: UnitOfWork = Depends()):
    import_job = uow.import_repository.get_by_id(import_id)
    if not import_job:
        raise HTTPException(status_code=404, detail="Import job not found")
    return import_job


@router.get("/type/{import_type}", response_model=List[ImportJobResponse])
def get_imports_by_type(import_type: str, uow: UnitOfWork = Depends()):
    imports = uow.import_repository.list_by_type(import_type)
    return imports


@router.get("/status/{status}", response_model=List[ImportJobResponse])
def get_imports_by_status(status: str, uow: UnitOfWork = Depends()):
    imports = uow.import_repository.list_by_status(status)
    return imports


@router.post("/", response_model=ImportJobResponse, status_code=201)
def create_import(import_job: ImportJobCreate, uow: UnitOfWork = Depends()):
    try:
        uow.import_repository.save(import_job)
        uow.commit()
        return uow.import_repository.get_by_id(import_job.id)
    except Exception as e:
        uow.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{import_id}", status_code=204)
def delete_import(import_id: int, uow: UnitOfWork = Depends()):
    existing_import = uow.import_repository.get_by_id(import_id)
    if not existing_import:
        raise HTTPException(status_code=404, detail="Import job not found")
    try:
        uow.import_repository.delete(import_id)
        uow.commit()
    except Exception as e:
        uow.rollback()
        raise HTTPException(status_code=400, detail=str(e))

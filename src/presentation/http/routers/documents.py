from typing import List

from fastapi import APIRouter, HTTPException, Depends
from src.presentation.schemas.document import (
    DocumentCreate,
    DocumentResponse,
    DocumentListResponse,
)
from src.infrastructure.db.unit_of_work import UnitOfWork

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("/", response_model=DocumentListResponse)
def list_documents(uow: UnitOfWork = Depends()):
    documents = uow.document_repository.list_all()
    return {"total": len(documents), "items": documents}


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, uow: UnitOfWork = Depends()):
    document = uow.document_repository.get_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.post("/", response_model=DocumentResponse, status_code=201)
def create_document(document: DocumentCreate, uow: UnitOfWork = Depends()):
    try:
        uow.document_repository.save(document)
        uow.commit()
        return uow.document_repository.get_by_id(document.id)
    except Exception as e:
        uow.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: int, uow: UnitOfWork = Depends()):
    existing_document = uow.document_repository.get_by_id(document_id)
    if not existing_document:
        raise HTTPException(status_code=404, detail="Document not found")
    try:
        uow.document_repository.delete(document_id)
        uow.commit()
    except Exception as e:
        uow.rollback()
        raise HTTPException(status_code=400, detail=str(e))

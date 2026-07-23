from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from src.infrastructure.db.models import Document as DocumentModel
from src.core.entities.document import Document, DocumentType, DocumentCategory


class DocumentRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, document: Document) -> None:
        model = self._to_model(document)
        self.session.add(model)
        self.session.flush()

    def get_by_id(self, id: int) -> Optional[Document]:
        model = self.session.get(DocumentModel, id)
        if model:
            return self._to_entity(model)
        return None

    def list_all(self) -> List[Document]:
        statement = select(DocumentModel)
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_by_asset(self, asset_id: int) -> List[Document]:
        statement = select(DocumentModel).where(DocumentModel.asset_id == asset_id)
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_by_entity(self, entity_id: int, entity_type: str) -> List[Document]:
        statement = select(DocumentModel).where(
            DocumentModel.entity_id == entity_id,
            DocumentModel.entity_type == entity_type
        )
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_by_type(self, document_type: DocumentType) -> List[Document]:
        statement = select(DocumentModel).where(
            DocumentModel.document_type == str(document_type.value)
        )
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_by_user(self, user_id: int) -> List[Document]:
        statement = select(DocumentModel).where(DocumentModel.uploaded_by == user_id)
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def get_primary_document(self, asset_id: int) -> Optional[Document]:
        statement = select(DocumentModel).where(
            DocumentModel.asset_id == asset_id,
            DocumentModel.is_primary == True
        )
        model = self.session.scalar(statement)
        if model:
            return self._to_entity(model)
        return None

    def count(self) -> int:
        statement = select(func.count(DocumentModel.id))
        return self.session.scalar(statement) or 0

    def _to_model(self, entity: Document) -> DocumentModel:
        return DocumentModel(
            id=entity.id,
            asset_id=entity.entity_id if entity.entity_type == 'asset' else None,
            document_type=str(entity.document_type.value) if entity.document_type else None,
            title=entity.title,
            description=entity.description,
            filename=entity.filename,
            file_path=entity.file_path,
            file_size=entity.file_size,
            mime_type=entity.mime_type,
            uploaded_by=entity.uploaded_by,
            entity_id=entity.entity_id,
            entity_type=entity.entity_type,
            uploaded_at=entity.uploaded_at,
            is_primary=entity.is_primary,
            sort_order=entity.sort_order,
            file_hash=entity.file_hash,
        )

    def _to_entity(self, model: DocumentModel) -> Document:
        return Document(
            id=model.id,
            filename=model.filename,
            file_path=model.file_path,
            file_size=model.file_size,
            mime_type=model.mime_type,
            uploaded_by=model.uploaded_by,
            document_type=DocumentType(model.document_type) if model.document_type else DocumentType.OTHER,
            category=DocumentCategory(model.category) if hasattr(model, 'category') and model.category else DocumentCategory.ASSET,
            entity_id=model.entity_id,
            entity_type=model.entity_type,
            title=model.title,
            description=model.description,
            uploaded_at=model.uploaded_at,
            is_primary=model.is_primary,
            sort_order=model.sort_order,
            file_hash=model.file_hash,
        )

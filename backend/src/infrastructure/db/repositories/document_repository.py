from typing import List, Tuple, Optional

from backend.src.infrastructure.db.models.document import Document as DocumentModel
from backend.src.core.entities.document import Document, DocumentType, DocumentCategory
from backend.src.use_cases.interfaces.repositories import IDocumentRepository


class DocumentRepository(IDocumentRepository):
    """Реализация репозитория для работы с документами"""

    def __init__(self, session):
        self.session = session

    async def get_all(self, skip: int = 0, limit: int = 100) -> Tuple[List[Document], int]:
        query = self.session.query(DocumentModel)
        total = query.count()
        documents = query.offset(skip).limit(limit).all()
        
        return [self._to_entity(doc) for doc in documents], total

    async def get_by_id(self, document_id: int) -> Optional[Document]:
        document = self.session.query(DocumentModel).filter(DocumentModel.id == document_id).first()
        if not document:
            return None
        return self._to_entity(document)

    async def add(self, document: Document) -> int:
        db_document = DocumentModel(
            filename=document.filename,
            file_path=document.file_path,
            file_size=document.file_size,
            mime_type=document.mime_type,
            uploaded_by=document.uploaded_by,
            document_type=document.document_type,
            category=document.category,
            entity_id=document.entity_id,
            entity_type=document.entity_type,
            title=document.title,
            description=document.description,
            is_primary=document.is_primary,
            sort_order=document.sort_order,
            file_hash=document.file_hash,
        )
        self.session.add(db_document)
        self.session.flush()
        return db_document.id

    async def delete(self, document_id: int) -> None:
        document = self.session.query(DocumentModel).filter(DocumentModel.id == document_id).first()
        if document:
            self.session.delete(document)

    async def get_by_entity(self, entity_id: int, entity_type: str) -> List[Document]:
        documents = (
            self.session.query(DocumentModel)
            .filter(
                DocumentModel.entity_id == entity_id,
                DocumentModel.entity_type == entity_type,
            )
            .all()
        )
        return [self._to_entity(doc) for doc in documents]

    def _to_entity(self, model: DocumentModel) -> Document:
        return Document(
            id=model.id,
            filename=model.filename,
            file_path=model.file_path,
            file_size=model.file_size,
            mime_type=model.mime_type,
            uploaded_by=model.uploaded_by,
            document_type=model.document_type,
            category=model.category,
            entity_id=model.entity_id,
            entity_type=model.entity_type,
            title=model.title,
            description=model.description,
            uploaded_at=model.uploaded_at,
            is_primary=model.is_primary,
            sort_order=model.sort_order,
            file_hash=model.file_hash,
        )

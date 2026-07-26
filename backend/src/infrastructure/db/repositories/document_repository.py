from src.infrastructure.db.models.document import Document as DocumentModel
from src.core.entities.document import Document, DocumentType, DocumentCategory
from src.use_cases.interfaces.repositories import IDocumentRepository


class DocumentRepository(IDocumentRepository):
    """Repository for document operations"""
    pass

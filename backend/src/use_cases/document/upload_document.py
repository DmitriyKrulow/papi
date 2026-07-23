from typing import TYPE_CHECKING
from pathlib import Path
import uuid

from backend.src.core.entities.document import DocumentType, DocumentCategory

if TYPE_CHECKING:
    from backend.src.use_cases.interfaces.unit_of_work import IUnitOfWork


class UploadDocumentService:
    def __init__(self, unit_of_work: "IUnitOfWork"):
        self.uow = unit_of_work

    async def __call__(self, file, uploaded_by: int, data: dict):
        file_path = await self._save_file(file)
        
        document_type = data.get("document_type", "other")
        category = data.get("category", "asset")
        
        try:
            dt = DocumentType(document_type)
        except ValueError:
            dt = DocumentType.OTHER
        
        try:
            dc = DocumentCategory(category)
        except ValueError:
            dc = DocumentCategory.ASSET
        
        document_id = await self.uow.documents.add(
            filename=file.filename,
            file_path=str(file_path),
            file_size=file.size,
            mime_type=file.content_type,
            uploaded_by=uploaded_by,
            document_type=dt,
            category=dc,
            entity_id=data.get("entity_id"),
            entity_type=data.get("entity_type"),
            title=data.get("title"),
            description=data.get("description"),
            is_primary=data.get("is_primary", False),
            sort_order=data.get("sort_order", 0),
            file_hash=None,
        )
        
        await self.uow.commit()
        
        return document_id

    async def _save_file(self, file) -> Path:
        upload_dir = Path("uploads/documents")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_id = uuid.uuid4().hex
        file_extension = Path(file.filename).suffix
        filename = f"{file_id}{file_extension}"
        
        file_path = upload_dir / filename
        
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        return file_path

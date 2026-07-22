# src/core/exceptions/document.py
from src.core.exceptions.base import (
    DomainException,
    NotFoundException,
    ValidationException,
)


class DocumentNotFoundException(NotFoundException):
    """Документ не найден"""
    def __init__(self, document_id: int):
        super().__init__("Document", document_id)


class DocumentUploadException(DomainException):
    """Ошибка загрузки документа"""
    def __init__(self, filename: str, reason: str):
        super().__init__(
            message=f"Failed to upload document '{filename}': {reason}",
            code="DOCUMENT_UPLOAD_ERROR",
            details={'filename': filename, 'reason': reason},
        )


class DocumentTooLargeException(ValidationException):
    """Документ слишком большой"""
    def __init__(self, max_size_mb: int):
        super().__init__(
            message=f"Document size exceeds maximum of {max_size_mb} MB",
            field="file",
        )


class InvalidFileTypeException(ValidationException):
    """Недопустимый тип файла"""
    def __init__(self, allowed_types: list):
        super().__init__(
            message=f"Invalid file type. Allowed: {', '.join(allowed_types)}",
            field="file",
        )
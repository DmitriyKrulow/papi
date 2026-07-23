# tests/unit/test_document.py
import pytest
from backend.src.core.entities.document import Document, DocumentType, DocumentCategory
from backend.src.core.entities.asset import Asset


class TestDocumentEntity:
    """Тесты сущности Document"""

    def test_create_document_with_valid_data(self):
        """Создание документа с валидными данными"""
        document = Document(
            id=1,
            filename="contract_001.pdf",
            file_path="/uploads/contract_001.pdf",
            file_size=102400,
            mime_type="application/pdf",
            uploaded_by=1
        )
        
        assert document.id == 1
        assert document.filename == "contract_001.pdf"
        assert document.file_size == 102400

    def test_document_with_optional_fields(self):
        """Документ с дополнительными полями"""
        document = Document(
            id=2,
            filename="invoice_001.xlsx",
            file_path="/uploads/invoice_001.xlsx",
            file_size=51200,
            mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            uploaded_by=1,
            document_type=DocumentType.INVOICE,
            category=DocumentCategory.CONTRACT,
            title="Счет-фактура №1",
            description="Счет за поставку оборудования",
            is_primary=True
        )
        
        assert document.document_type == DocumentType.INVOICE
        assert document.category == DocumentCategory.CONTRACT
        assert document.title == "Счет-фактура №1"
        assert document.is_primary is True

    def test_get_file_extension(self):
        """Получение расширения файла"""
        document = Document(
            id=3,
            filename="manual.pdf",
            file_path="/uploads/manual.pdf",
            file_size=204800,
            mime_type="application/pdf",
            uploaded_by=1
        )
        
        assert document.get_file_extension() == "pdf"

    def test_get_file_size_display(self):
        """Читаемый размер файла"""
        document = Document(
            id=4,
            filename="small.txt",
            file_path="/uploads/small.txt",
            file_size=512,
            mime_type="text/plain",
            uploaded_by=1
        )
        
        assert document.get_file_size_display() == "512 B"

    def test_is_image(self):
        """Проверка, является ли файл изображением"""
        document = Document(
            id=5,
            filename="photo.jpg",
            file_path="/uploads/photo.jpg",
            file_size=1024000,
            mime_type="image/jpeg",
            uploaded_by=1
        )
        
        assert document.is_image() is True

    def test_is_pdf(self):
        """Проверка, является ли файл PDF"""
        document = Document(
            id=6,
            filename="report.pdf",
            file_path="/uploads/report.pdf",
            file_size=500000,
            mime_type="application/pdf",
            uploaded_by=1
        )
        
        assert document.is_pdf() is True

    def test_document_str_representation(self):
        """Строковое представление документа"""
        document = Document(
            id=7,
            filename="document.docx",
            file_path="/uploads/document.docx",
            file_size=25600,
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            uploaded_by=1
        )
        
        assert "document.docx" in str(document)

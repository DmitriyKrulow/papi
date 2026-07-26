# backend/src/infrastructure/db/repositories/__init__.py

from .user_repository import InMemoryUserRepository
from .repair_request_repository import RepairRequestRepository
from .repair_template_repository import RepairTemplateRepository
from .asset_photo_repository import AssetPhotoRepository
from .document_repository import DocumentRepository

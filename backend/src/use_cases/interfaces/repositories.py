from abc import ABC, abstractmethod
from typing import List, Tuple, Optional

from backend.src.core.entities.document import Document
from backend.src.core.entities.asset_photo import AssetPhoto
from backend.src.core.entities.user import User


class IDocumentRepository(ABC):
    """Абстрактный репозиторий для работы с документами"""

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> Tuple[List[Document], int]:
        """Получить все документы с пагинацией"""
        pass

    @abstractmethod
    async def get_by_id(self, document_id: int) -> Optional[Document]:
        """Получить документ по ID"""
        pass

    @abstractmethod
    async def add(self, document: Document) -> int:
        """Добавить новый документ"""
        pass

    @abstractmethod
    async def delete(self, document_id: int) -> None:
        """Удалить документ"""
        pass

    @abstractmethod
    async def get_by_entity(self, entity_id: int, entity_type: str) -> List[Document]:
        """Получить документы по сущности"""
        pass


class IAssetPhotoRepository(ABC):
    """Абстрактный репозиторий для работы с фотографиями активов"""

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> Tuple[List[AssetPhoto], int]:
        """Получить все фотографии с пагинацией"""
        pass

    @abstractmethod
    async def get_by_id(self, photo_id: int) -> Optional[AssetPhoto]:
        """Получить фото по ID"""
        pass

    @abstractmethod
    async def add(self, photo: AssetPhoto) -> int:
        """Добавить новое фото"""
        pass

    @abstractmethod
    async def delete(self, photo_id: int) -> None:
        """Удалить фото"""
        pass

    @abstractmethod
    async def get_by_asset(self, asset_id: int) -> List[AssetPhoto]:
        """Получить фотографии актива"""
        pass


class IUserRepository(ABC):
    """Абстрактный репозиторий для работы с пользователями"""

    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """Получить пользователя по username"""
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Получить пользователя по email"""
        pass

    @abstractmethod
    async def create(self, user: User) -> User:
        """Создать нового пользователя"""
        pass

    @abstractmethod
    async def update(self, user: User) -> User:
        """Обновить пользователя"""
        pass

    @abstractmethod
    async def delete(self, user_id: int) -> None:
        """Удалить пользователя"""
        pass

from contextlib import contextmanager
from typing import Generator, Optional, Callable, Any
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from src.infrastructure.db.models import Base
from src.infrastructure.db.repositories import (
    AssetRepository,
    UserRepository,
    RepairRepository,
    DocumentRepository,
    EmployeeRepository,
    DepartmentRepository,
    MovementRepository,
    MaintenanceRepository,
    DepreciationRepository,
    InventoryRepository,
    ImportRepository,
    AssetPhotoRepository,
)


class UnitOfWork:
    def __init__(self, session_factory: sessionmaker[Session]):
        self.session_factory = session_factory
        self._session: Optional[Session] = None
        self.committed = False
        self.rolled_back = False

    @contextmanager
    def start(self) -> Generator['UnitOfWork', None, None]:
        self._session = self.session_factory()
        try:
            yield self
            if not self.rolled_back:
                self.commit()
        except Exception:
            self.rollback()
            raise
        finally:
            self._session.close()
            self._session = None

    def commit(self) -> None:
        if self._session:
            try:
                self._session.commit()
                self.committed = True
            except Exception:
                self.rollback()
                raise

    def rollback(self) -> None:
        if self._session:
            self._session.rollback()
            self.rolled_back = True

    @property
    def asset_repository(self) -> AssetRepository:
        return AssetRepository(self._session)

    @property
    def user_repository(self) -> UserRepository:
        return UserRepository(self._session)

    @property
    def repair_repository(self) -> RepairRepository:
        return RepairRepository(self._session)

    @property
    def document_repository(self) -> DocumentRepository:
        return DocumentRepository(self._session)

    @property
    def employee_repository(self) -> EmployeeRepository:
        return EmployeeRepository(self._session)

    @property
    def department_repository(self) -> DepartmentRepository:
        return DepartmentRepository(self._session)

    @property
    def movement_repository(self) -> MovementRepository:
        return MovementRepository(self._session)

    @property
    def maintenance_repository(self) -> MaintenanceRepository:
        return MaintenanceRepository(self._session)

    @property
    def depreciation_repository(self) -> DepreciationRepository:
        return DepreciationRepository(self._session)

    @property
    def inventory_repository(self) -> InventoryRepository:
        return InventoryRepository(self._session)

    @property
    def import_repository(self) -> ImportRepository:
        return ImportRepository(self._session)

    @property
    def asset_photo_repository(self) -> AssetPhotoRepository:
        return AssetPhotoRepository(self._session)


def create_session_factory(database_url: str, echo: bool = False) -> sessionmaker[Session]:
    engine = create_engine(database_url, echo=echo)
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_unit_of_work(database_url: str, echo: bool = False) -> UnitOfWork:
    session_factory = create_session_factory(database_url, echo)
    return UnitOfWork(session_factory)

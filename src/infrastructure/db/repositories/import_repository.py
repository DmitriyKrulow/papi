from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from src.infrastructure.db.models import ImportJob as ImportJobModel
from src.core.entities.import_job import ImportJob, ImportStatus, ImportType


class ImportRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, job: ImportJob) -> None:
        model = self._to_model(job)
        self.session.add(model)
        self.session.flush()

    def get_by_id(self, id: int) -> Optional[ImportJob]:
        model = self.session.get(ImportJobModel, id)
        if model:
            return self._to_entity(model)
        return None

    def list_all(self) -> List[ImportJob]:
        statement = select(ImportJobModel)
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_by_type(self, import_type: ImportType) -> List[ImportJob]:
        statement = select(ImportJobModel).where(ImportJobModel.import_type == str(import_type.value))
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_by_status(self, status: ImportStatus) -> List[ImportJob]:
        statement = select(ImportJobModel).where(ImportJobModel.status == str(status.value))
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_by_user(self, user_id: int) -> List[ImportJob]:
        statement = select(ImportJobModel).where(ImportJobModel.created_by == user_id)
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_pending(self) -> List[ImportJob]:
        statement = select(ImportJobModel).where(ImportJobModel.status == str(ImportStatus.PENDING.value))
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_processing(self) -> List[ImportJob]:
        statement = select(ImportJobModel).where(ImportJobModel.status == str(ImportStatus.PROCESSING.value))
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def count(self) -> int:
        statement = select(func.count(ImportJobModel.id))
        return self.session.scalar(statement) or 0

    def _to_model(self, entity: ImportJob) -> ImportJobModel:
        return ImportJobModel(
            id=entity.id,
            filename=entity.filename,
            import_type=str(entity.import_type.value) if entity.import_type else None,
            created_by=entity.created_by,
            status=str(entity.status.value) if entity.status else None,
            total_rows=entity.total_rows,
            processed_rows=entity.processed_rows,
            successful_rows=entity.successful_rows,
            failed_rows=entity.failed_rows,
            errors=str(entity.errors) if entity.errors else None,
            error_file_id=entity.error_file_id,
            result_file_id=entity.result_file_id,
            summary=str(entity.summary) if entity.summary else None,
            created_at=entity.created_at,
            started_at=entity.started_at,
            completed_at=entity.completed_at,
            parameters=str(entity.parameters) if entity.parameters else None,
        )

    def _to_entity(self, model: ImportJobModel) -> ImportJob:
        errors = []
        if model.errors:
            try:
                import json
                errors = json.loads(model.errors)
            except (json.JSONDecodeError, TypeError):
                errors = []

        summary = {}
        if model.summary:
            try:
                import json
                summary = json.loads(model.summary)
            except (json.JSONDecodeError, TypeError):
                summary = {}

        parameters = {}
        if model.parameters:
            try:
                import json
                parameters = json.loads(model.parameters)
            except (json.JSONDecodeError, TypeError):
                parameters = {}

        return ImportJob(
            id=model.id,
            filename=model.filename,
            import_type=ImportType(model.import_type) if model.import_type else ImportType.ASSETS,
            created_by=model.created_by,
            status=ImportStatus(model.status) if model.status else ImportStatus.PENDING,
            total_rows=model.total_rows,
            processed_rows=model.processed_rows,
            successful_rows=model.successful_rows,
            failed_rows=model.failed_rows,
            errors=errors,
            error_file_id=model.error_file_id,
            result_file_id=model.result_file_id,
            summary=summary,
            created_at=model.created_at,
            started_at=model.started_at,
            completed_at=model.completed_at,
            parameters=parameters,
        )

from typing import Optional, List

from src.infrastructure.db.models.repair_template import RepairTemplate


class RepairTemplateRepository:
    def __init__(self, db_session):
        self.db_session = db_session

    def get_by_id(self, template_id: int) -> Optional[RepairTemplate]:
        return self.db_session.query(RepairTemplate).filter(RepairTemplate.id == template_id).first()

    def get_all(self, active_only: bool = True) -> List[RepairTemplate]:
        query = self.db_session.query(RepairTemplate)
        if active_only:
            query = query.filter(RepairTemplate.is_active == True)
        return query.all()

    def get_default_template(self) -> Optional[RepairTemplate]:
        return self.db_session.query(RepairTemplate).filter(RepairTemplate.is_default == True).first()

    def create(self, template_data: dict) -> RepairTemplate:
        template = RepairTemplate(
            name=template_data.get("name", ""),
            description=template_data.get("description", ""),
            template_data=template_data.get("template_data", {}),
            is_active=template_data.get("is_active", True),
            is_default=template_data.get("is_default", False),
            created_by=template_data.get("created_by"),
            created_at=template_data.get("created_at"),
            updated_at=template_data.get("updated_at"),
        )
        self.db_session.add(template)
        self.db_session.commit()
        self.db_session.refresh(template)
        return template

    def update(self, template_id: int, template_data: dict) -> Optional[RepairTemplate]:
        template = self.get_by_id(template_id)
        if not template:
            return None

        for key, value in template_data.items():
            if hasattr(template, key) and key != "id":
                setattr(template, key, value)

        template.updated_at = template_data.get("updated_at")

        self.db_session.commit()
        self.db_session.refresh(template)
        return template

    def delete(self, template_id: int) -> bool:
        template = self.get_by_id(template_id)
        if not template:
            return False

        self.db_session.delete(template)
        self.db_session.commit()
        return True

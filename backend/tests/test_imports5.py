import sys
sys.path.insert(0, 'backend/src')

from infrastructure.db.models.repair_request import RepairRequest, RepairStatus, RepairPriority
from infrastructure.db.models.repair_template import RepairTemplate
from infrastructure.db.models.asset import Asset
from infrastructure.db.models.user import User
from core.entities.repair_request import RepairRequest as CoreRepairRequest, RepairStatus as CoreRepairStatus, RepairPriority as CoreRepairPriority
from core.entities.repair_template import RepairTemplate as CoreRepairTemplate
from infrastructure.db.repositories.repair_request_repository import RepairRequestRepository
from infrastructure.db.repositories.repair_template_repository import RepairTemplateRepository
from infrastructure.reports.repair_report import RepairReportGenerator
from presentation.http.schemas.repairs import (
    RepairRequestCreate, RepairRequestResponse, RepairRequestUpdate,
    RepairStatusUpdate, RepairPriorityUpdate,
    RepairTemplateCreate, RepairTemplateResponse, RepairTemplateUpdate, RepairTemplateApply
)
from infrastructure.services.repair_print_service import RepairPrintService

print('All imports successful!')

"""FactoryOps v1 REST endpoints backed only by application services."""

from datetime import timezone

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import text

from factoryops import __version__
from factoryops.application.services import (
    BatchService,
    InspectionService,
    PartService,
    QualityService,
    SupplierService,
)
from factoryops.domain.entities import CorrectiveAction, InspectionRecord, QualityCase

from .schemas import (
    BatchContextRead,
    BatchRead,
    CorrectiveActionCreate,
    CorrectiveActionRead,
    DataResponse,
    HealthRead,
    InspectionCreate,
    InspectionRead,
    PartDetail,
    PartRead,
    PartVehicleImpactRead,
    QualityCaseCreate,
    QualityCaseDetailRead,
    QualityCaseRead,
    SupplierDetail,
    SupplierRead,
    VehicleImpactRead,
)

router = APIRouter(prefix="/api/v1")


def uow_factory(request: Request):
    return request.app.state.uow_factory


def supplier_service(factory=Depends(uow_factory)) -> SupplierService:
    return SupplierService(factory)


def part_service(factory=Depends(uow_factory)) -> PartService:
    return PartService(factory)


def batch_service(factory=Depends(uow_factory)) -> BatchService:
    return BatchService(factory)


def inspection_service(factory=Depends(uow_factory)) -> InspectionService:
    return InspectionService(factory)


def quality_service(factory=Depends(uow_factory)) -> QualityService:
    return QualityService(factory)


@router.get("/health", response_model=DataResponse[HealthRead])
def health(request: Request):
    database = "reachable"
    try:
        with request.app.state.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        database = "unreachable"
    return DataResponse(
        data=HealthRead(
            status="ok" if database == "reachable" else "degraded",
            service="factoryops-api",
            version=__version__,
            database=database,
        )
    )


@router.get("/suppliers", response_model=DataResponse[list[SupplierRead]])
def list_suppliers(service: SupplierService = Depends(supplier_service)):
    return DataResponse(data=service.list_suppliers())


@router.get("/suppliers/{supplier_code}", response_model=DataResponse[SupplierDetail])
def get_supplier(supplier_code: str, service: SupplierService = Depends(supplier_service)):
    supplier = service.get_supplier(supplier_code)
    parts = service.get_supplier_parts(supplier_code)
    return DataResponse(data=SupplierDetail(supplier=supplier, parts=parts))


@router.get("/parts", response_model=DataResponse[list[PartRead]])
def list_parts(service: PartService = Depends(part_service)):
    return DataResponse(data=service.list_parts())


@router.get("/parts/{part_number}", response_model=DataResponse[PartDetail])
def get_part(part_number: str, service: PartService = Depends(part_service)):
    part = service.get_part(part_number)
    suppliers = service.get_part_suppliers(part_number)
    impact = service.get_part_vehicle_impact(part_number)
    return DataResponse(
        data=PartDetail(
            part=part,
            suppliers=suppliers,
            vehicle_models=[
                VehicleImpactRead(
                    vehicle_model=item.vehicle_model,
                    bom_versions=list(item.bom_versions),
                )
                for item in impact.vehicle_models
            ],
        )
    )


@router.get(
    "/parts/{part_number}/vehicle-impact",
    response_model=DataResponse[PartVehicleImpactRead],
)
def get_part_vehicle_impact(part_number: str, service: PartService = Depends(part_service)):
    impact = service.get_part_vehicle_impact(part_number)
    return DataResponse(
        data=PartVehicleImpactRead(
            part=impact.part,
            vehicle_models=[
                VehicleImpactRead(
                    vehicle_model=item.vehicle_model,
                    bom_versions=list(item.bom_versions),
                )
                for item in impact.vehicle_models
            ],
        )
    )


@router.get("/batches/{batch_number}", response_model=DataResponse[BatchRead])
def get_batch(batch_number: str, service: BatchService = Depends(batch_service)):
    return DataResponse(data=service.get_batch(batch_number))


@router.get(
    "/batches/{batch_number}/context", response_model=DataResponse[BatchContextRead]
)
def get_batch_context(batch_number: str, service: BatchService = Depends(batch_service)):
    context = service.get_batch_context(batch_number)
    return DataResponse(
        data=BatchContextRead(
            batch=context.batch,
            part=context.part,
            supplier=context.supplier,
            inspection_summary={
                "total": context.inspection_summary.total,
                "passed": context.inspection_summary.passed,
                "failed": context.inspection_summary.failed,
                "records": list(context.inspection_summary.records),
            },
            related_quality_issues=list(context.related_quality_issues),
        )
    )


@router.get(
    "/batches/{batch_number}/inspections", response_model=DataResponse[list[InspectionRead]]
)
def list_batch_inspections(
    batch_number: str, service: InspectionService = Depends(inspection_service)
):
    return DataResponse(data=service.list_batch_inspections(batch_number))


@router.post(
    "/batches/{batch_number}/inspections",
    status_code=status.HTTP_201_CREATED,
    response_model=DataResponse[InspectionRead],
)
def create_inspection(
    batch_number: str,
    payload: InspectionCreate,
    batches: BatchService = Depends(batch_service),
    inspections: InspectionService = Depends(inspection_service),
):
    batch = batches.get_batch(batch_number)
    inspection = InspectionRecord.create(
        inspection_number=payload.inspection_number,
        batch_id=batch.id,
        process_id=payload.process_id,
        inspection_type=payload.inspection_type,
        metric_name=payload.metric_name,
        measured_value=payload.measured_value,
        lower_limit=payload.lower_limit,
        upper_limit=payload.upper_limit,
        inspected_at=payload.inspected_at,
    )
    return DataResponse(data=inspections.create_inspection_record(inspection))


@router.get("/quality-cases", response_model=DataResponse[list[QualityCaseRead]])
def list_quality_cases(service: QualityService = Depends(quality_service)):
    return DataResponse(data=service.list_quality_cases())


@router.get(
    "/quality-cases/{case_number}", response_model=DataResponse[QualityCaseDetailRead]
)
def get_quality_case(case_number: str, service: QualityService = Depends(quality_service)):
    detail = service.get_quality_case(case_number)
    return DataResponse(
        data=QualityCaseDetailRead(
            quality_case=detail.quality_case,
            issues=list(detail.issues),
            corrective_actions=list(detail.corrective_actions),
        )
    )


@router.post(
    "/quality-cases",
    status_code=status.HTTP_201_CREATED,
    response_model=DataResponse[QualityCaseRead],
)
def create_quality_case(
    payload: QualityCaseCreate, service: QualityService = Depends(quality_service)
):
    quality_case = QualityCase(
        case_number=payload.case_number,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        status=payload.status,
        owner=payload.owner,
        opened_at=payload.opened_at,
    )
    return DataResponse(data=service.create_quality_case(quality_case))


@router.post(
    "/quality-cases/{case_number}/issues/{issue_number}",
    response_model=DataResponse[QualityCaseDetailRead],
)
def add_issue_to_case(
    case_number: str,
    issue_number: str,
    service: QualityService = Depends(quality_service),
):
    detail = service.add_issue_to_case(case_number, issue_number)
    return DataResponse(
        data=QualityCaseDetailRead(
            quality_case=detail.quality_case,
            issues=list(detail.issues),
            corrective_actions=list(detail.corrective_actions),
        )
    )


@router.post(
    "/quality-cases/{case_number}/actions",
    status_code=status.HTTP_201_CREATED,
    response_model=DataResponse[CorrectiveActionRead],
)
def create_corrective_action(
    case_number: str,
    payload: CorrectiveActionCreate,
    service: QualityService = Depends(quality_service),
):
    detail = service.get_quality_case(case_number)
    action = CorrectiveAction(
        action_number=payload.action_number,
        quality_case_id=detail.quality_case.id,
        title=payload.title,
        description=payload.description,
        action_type=payload.action_type,
        status=payload.status,
        assignee=payload.assignee,
        due_date=payload.due_date,
    )
    return DataResponse(data=service.create_corrective_action(case_number, action))

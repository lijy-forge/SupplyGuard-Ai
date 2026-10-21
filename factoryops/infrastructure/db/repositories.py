"""SQLAlchemy implementations of FactoryOps repository ports."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from factoryops.application.dto import (
    BatchContext,
    InspectionSummary,
    PartVehicleImpact,
    QualityCaseDetail,
    VehicleImpact,
)
from factoryops.application.ports import (
    BatchRepository,
    InspectionRepository,
    PartRepository,
    QualityCaseRepository,
    SupplierRepository,
)
from factoryops.domain.entities import (
    Batch,
    CorrectiveAction,
    InspectionRecord,
    Part,
    QualityCase,
    QualityIssue,
    Supplier,
    VehicleModel,
)

from .models import (
    BOMItemModel,
    BatchModel,
    CorrectiveActionModel,
    InspectionRecordModel,
    PartModel,
    QualityCaseIssueModel,
    QualityCaseModel,
    QualityIssueBatchModel,
    QualityIssueModel,
    SupplierModel,
    SupplierPartModel,
    VehicleModelModel,
)


def to_supplier(row: SupplierModel) -> Supplier:
    return Supplier(
        id=row.id,
        record_version=row.record_version,
        supplier_code=row.supplier_code,
        name=row.name,
        category=row.category,
        country=row.country,
        status=row.status,
        risk_level=row.risk_level,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def to_part(row: PartModel) -> Part:
    return Part(
        id=row.id,
        record_version=row.record_version,
        part_number=row.part_number,
        name=row.name,
        category=row.category,
        specification=row.specification,
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def to_vehicle_model(row: VehicleModelModel) -> VehicleModel:
    return VehicleModel(
        id=row.id,
        record_version=row.record_version,
        model_code=row.model_code,
        name=row.name,
        platform=row.platform,
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def to_batch(row: BatchModel) -> Batch:
    return Batch(
        id=row.id,
        record_version=row.record_version,
        batch_number=row.batch_number,
        part_id=row.part_id,
        supplier_id=row.supplier_id,
        manufactured_at=row.manufactured_at,
        received_at=row.received_at,
        quantity=row.quantity,
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def to_inspection(row: InspectionRecordModel) -> InspectionRecord:
    return InspectionRecord(
        id=row.id,
        record_version=row.record_version,
        inspection_number=row.inspection_number,
        batch_id=row.batch_id,
        process_id=row.process_id,
        inspection_type=row.inspection_type,
        metric_name=row.metric_name,
        measured_value=row.measured_value,
        lower_limit=row.lower_limit,
        upper_limit=row.upper_limit,
        result=row.result,
        inspected_at=row.inspected_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def to_issue(row: QualityIssueModel) -> QualityIssue:
    return QualityIssue(
        id=row.id,
        record_version=row.record_version,
        issue_number=row.issue_number,
        title=row.title,
        description=row.description,
        severity=row.severity,
        status=row.status,
        detected_at=row.detected_at,
        source=row.source,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def to_case(row: QualityCaseModel) -> QualityCase:
    return QualityCase(
        id=row.id,
        record_version=row.record_version,
        case_number=row.case_number,
        title=row.title,
        description=row.description,
        priority=row.priority,
        status=row.status,
        owner=row.owner,
        opened_at=row.opened_at,
        closed_at=row.closed_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def to_action(row: CorrectiveActionModel) -> CorrectiveAction:
    return CorrectiveAction(
        id=row.id,
        record_version=row.record_version,
        action_number=row.action_number,
        quality_case_id=row.quality_case_id,
        title=row.title,
        description=row.description,
        action_type=row.action_type,
        status=row.status,
        assignee=row.assignee,
        due_date=row.due_date,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemySupplierRepository(SupplierRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self) -> list[Supplier]:
        rows = self.session.scalars(
            select(SupplierModel).order_by(SupplierModel.supplier_code)
        ).all()
        return [to_supplier(row) for row in rows]

    def get_by_code(self, supplier_code: str) -> Supplier | None:
        row = self.session.scalar(
            select(SupplierModel).where(SupplierModel.supplier_code == supplier_code)
        )
        return to_supplier(row) if row else None

    def get_parts(self, supplier_id: str) -> list[Part]:
        rows = self.session.scalars(
            select(PartModel)
            .join(SupplierPartModel, SupplierPartModel.part_id == PartModel.id)
            .where(SupplierPartModel.supplier_id == supplier_id)
            .order_by(PartModel.part_number)
        ).all()
        return [to_part(row) for row in rows]


class SqlAlchemyPartRepository(PartRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self) -> list[Part]:
        rows = self.session.scalars(select(PartModel).order_by(PartModel.part_number)).all()
        return [to_part(row) for row in rows]

    def get_by_number(self, part_number: str) -> Part | None:
        row = self.session.scalar(
            select(PartModel).where(PartModel.part_number == part_number)
        )
        return to_part(row) if row else None

    def get_suppliers(self, part_id: str) -> list[Supplier]:
        rows = self.session.scalars(
            select(SupplierModel)
            .join(SupplierPartModel, SupplierPartModel.supplier_id == SupplierModel.id)
            .where(SupplierPartModel.part_id == part_id)
            .order_by(SupplierModel.supplier_code)
        ).all()
        return [to_supplier(row) for row in rows]

    def get_vehicle_impact(self, part_number: str) -> PartVehicleImpact | None:
        part_row = self.session.scalar(
            select(PartModel).where(PartModel.part_number == part_number)
        )
        if part_row is None:
            return None
        rows = self.session.execute(
            select(VehicleModelModel, BOMItemModel.bom_version)
            .join(BOMItemModel, BOMItemModel.vehicle_model_id == VehicleModelModel.id)
            .where(BOMItemModel.part_id == part_row.id)
            .order_by(VehicleModelModel.model_code, BOMItemModel.bom_version)
        ).all()
        grouped: dict[str, tuple[VehicleModelModel, list[str]]] = {}
        for vehicle, version in rows:
            if vehicle.id not in grouped:
                grouped[vehicle.id] = (vehicle, [])
            if version not in grouped[vehicle.id][1]:
                grouped[vehicle.id][1].append(version)
        impacts = tuple(
            VehicleImpact(to_vehicle_model(vehicle), tuple(versions))
            for vehicle, versions in grouped.values()
        )
        return PartVehicleImpact(part=to_part(part_row), vehicle_models=impacts)


class SqlAlchemyInspectionRepository(InspectionRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, inspection: InspectionRecord) -> InspectionRecord:
        self.session.add(
            InspectionRecordModel(
                id=inspection.id,
                inspection_number=inspection.inspection_number,
                batch_id=inspection.batch_id,
                process_id=inspection.process_id,
                inspection_type=inspection.inspection_type,
                metric_name=inspection.metric_name,
                measured_value=inspection.measured_value,
                lower_limit=inspection.lower_limit,
                upper_limit=inspection.upper_limit,
                result=inspection.result,
                inspected_at=inspection.inspected_at,
                created_at=inspection.created_at,
                updated_at=inspection.updated_at,
            )
        )
        return inspection

    def list_for_batch(self, batch_id: str) -> list[InspectionRecord]:
        rows = self.session.scalars(
            select(InspectionRecordModel)
            .where(InspectionRecordModel.batch_id == batch_id)
            .order_by(InspectionRecordModel.inspected_at, InspectionRecordModel.inspection_number)
        ).all()
        return [to_inspection(row) for row in rows]


class SqlAlchemyBatchRepository(BatchRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_number(self, batch_number: str) -> Batch | None:
        row = self.session.scalar(
            select(BatchModel).where(BatchModel.batch_number == batch_number)
        )
        return to_batch(row) if row else None

    def get_context(self, batch_number: str) -> BatchContext | None:
        row = self.session.execute(
            select(BatchModel, PartModel, SupplierModel)
            .join(PartModel, PartModel.id == BatchModel.part_id)
            .join(SupplierModel, SupplierModel.id == BatchModel.supplier_id)
            .where(BatchModel.batch_number == batch_number)
        ).first()
        if row is None:
            return None
        batch_row, part_row, supplier_row = row
        inspections = [
            to_inspection(item)
            for item in self.session.scalars(
                select(InspectionRecordModel)
                .where(InspectionRecordModel.batch_id == batch_row.id)
                .order_by(InspectionRecordModel.inspection_number)
            ).all()
        ]
        issues = [
            to_issue(item)
            for item in self.session.scalars(
                select(QualityIssueModel)
                .join(
                    QualityIssueBatchModel,
                    QualityIssueBatchModel.quality_issue_id == QualityIssueModel.id,
                )
                .where(QualityIssueBatchModel.batch_id == batch_row.id)
                .order_by(QualityIssueModel.issue_number)
            ).all()
        ]
        passed = sum(item.result.value == "PASS" for item in inspections)
        return BatchContext(
            batch=to_batch(batch_row),
            part=to_part(part_row),
            supplier=to_supplier(supplier_row),
            inspection_summary=InspectionSummary(
                total=len(inspections),
                passed=passed,
                failed=len(inspections) - passed,
                records=tuple(inspections),
            ),
            related_quality_issues=tuple(issues),
        )


class SqlAlchemyQualityCaseRepository(QualityCaseRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, quality_case: QualityCase) -> QualityCase:
        self.session.add(
            QualityCaseModel(
                id=quality_case.id,
                case_number=quality_case.case_number,
                title=quality_case.title,
                description=quality_case.description,
                priority=quality_case.priority,
                status=quality_case.status,
                owner=quality_case.owner,
                opened_at=quality_case.opened_at,
                closed_at=quality_case.closed_at,
                created_at=quality_case.created_at,
                updated_at=quality_case.updated_at,
            )
        )
        return quality_case

    def list(self) -> list[QualityCase]:
        rows = self.session.scalars(
            select(QualityCaseModel).order_by(QualityCaseModel.case_number)
        ).all()
        return [to_case(row) for row in rows]

    def get_by_number(self, case_number: str) -> QualityCaseDetail | None:
        case_row = self.session.scalar(
            select(QualityCaseModel).where(QualityCaseModel.case_number == case_number)
        )
        if case_row is None:
            return None
        issues = self.session.scalars(
            select(QualityIssueModel)
            .join(
                QualityCaseIssueModel,
                QualityCaseIssueModel.quality_issue_id == QualityIssueModel.id,
            )
            .where(QualityCaseIssueModel.quality_case_id == case_row.id)
            .order_by(QualityIssueModel.issue_number)
        ).all()
        actions = self.session.scalars(
            select(CorrectiveActionModel)
            .where(CorrectiveActionModel.quality_case_id == case_row.id)
            .order_by(CorrectiveActionModel.action_number)
        ).all()
        return QualityCaseDetail(
            quality_case=to_case(case_row),
            issues=tuple(to_issue(row) for row in issues),
            corrective_actions=tuple(to_action(row) for row in actions),
        )

    def find_issue(self, issue_number: str) -> QualityIssue | None:
        row = self.session.scalar(
            select(QualityIssueModel).where(QualityIssueModel.issue_number == issue_number)
        )
        return to_issue(row) if row else None

    def associate_issue(self, quality_case_id: str, quality_issue_id: str) -> None:
        from factoryops.domain.entities import new_id

        self.session.add(
            QualityCaseIssueModel(
                id=new_id(),
                quality_case_id=quality_case_id,
                quality_issue_id=quality_issue_id,
            )
        )

    def add_action(self, action: CorrectiveAction) -> CorrectiveAction:
        self.session.add(
            CorrectiveActionModel(
                id=action.id,
                action_number=action.action_number,
                quality_case_id=action.quality_case_id,
                title=action.title,
                description=action.description,
                action_type=action.action_type,
                status=action.status,
                assignee=action.assignee,
                due_date=action.due_date,
                created_at=action.created_at,
                updated_at=action.updated_at,
            )
        )
        return action

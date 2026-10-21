"""Deterministic, wholly synthetic FactoryOps demonstration dataset."""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid5

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from factoryops.domain.enums import (
    CasePriority,
    CorrectiveActionStatus,
    DocumentType,
    InspectionResult,
    LifecycleStatus,
    QualityCaseStatus,
    QualityIssueStatus,
    QualitySeverity,
    SupplierRiskLevel,
    UserRole,
)

from .models import (
    BOMItemModel,
    BatchModel,
    CorrectiveActionModel,
    DocumentModel,
    InspectionRecordModel,
    PartModel,
    PlantModel,
    ProcessModel,
    QualityCaseIssueModel,
    QualityCaseModel,
    QualityIssueBatchModel,
    QualityIssueModel,
    SupplierModel,
    SupplierPartModel,
    UserModel,
    VehicleModelModel,
)

SEED_NAMESPACE = UUID("9bd33f8a-e606-4c86-9c7b-8851a38fa2bb")
SEED_TIMESTAMP = datetime(2026, 1, 5, 8, 0, tzinfo=timezone.utc)


def stable_id(kind: str, key: str) -> str:
    return str(uuid5(SEED_NAMESPACE, f"{kind}:{key}"))


def _base(kind: str, key: str) -> dict:
    return {
        "id": stable_id(kind, key),
        "record_version": 1,
        "created_at": SEED_TIMESTAMP,
        "updated_at": SEED_TIMESTAMP,
    }


def seed_database(session: Session) -> dict[str, int | str]:
    """Insert the canonical dataset once and return exact row counts."""
    existing = session.scalar(select(func.count()).select_from(SupplierModel))
    if existing:
        counts = seed_counts(session)
        counts["status"] = "already_seeded"
        return counts

    suppliers = []
    for index in range(1, 11):
        code = f"SUP-{index:03d}"
        suppliers.append(
            SupplierModel(
                **_base("supplier", code),
                supplier_code=code,
                name=f"Synthetic Components {index:02d}",
                category=("Machining", "Electronics", "Polymer", "Fasteners")[index % 4],
                country=("Freedonia", "Arcadia", "Northland")[index % 3],
                status=LifecycleStatus.ACTIVE,
                risk_level=(SupplierRiskLevel.LOW, SupplierRiskLevel.MEDIUM, SupplierRiskLevel.HIGH)[
                    index % 3
                ],
            )
        )
    session.add_all(suppliers)

    parts = []
    for index in range(1, 31):
        number = f"PART-{index:03d}"
        parts.append(
            PartModel(
                **_base("part", number),
                part_number=number,
                name=f"Synthetic Assembly Part {index:02d}",
                category=("Chassis", "Electrical", "Interior", "Thermal", "Powertrain")[
                    index % 5
                ],
                specification=f"DEMO-SPEC-{index:03d}; synthetic dimensional envelope",
                status=LifecycleStatus.ACTIVE,
            )
        )
    session.add_all(parts)

    model_codes = ("VM-A", "VM-B", "ALPHA-X", "ORION-S")
    vehicles = [
        VehicleModelModel(
            **_base("vehicle", code),
            model_code=code,
            name=f"Synthetic Vehicle {code}",
            platform=f"DEMO-P{index + 1}",
            status=LifecycleStatus.ACTIVE,
        )
        for index, code in enumerate(model_codes)
    ]
    session.add_all(vehicles)

    bom_items = []
    for model_index, vehicle in enumerate(vehicles):
        for offset in range(15):
            # Intentional overlap: PART-001 is used by VM-A and VM-B.
            part = parts[(model_index * 7 + offset) % len(parts)]
            key = f"{vehicle.model_code}:{part.part_number}:V1"
            bom_items.append(
                BOMItemModel(
                    **_base("bom", key),
                    vehicle_model_id=vehicle.id,
                    part_id=part.id,
                    quantity=Decimal("1") + Decimal(offset % 3),
                    bom_version="V1",
                    effective_from=date(2026, 1, 1),
                    effective_to=None,
                )
            )
    # Ensure CASE-001's PART-001 has two vehicle impacts even if loop changes.
    existing_pairs = {(row.vehicle_model_id, row.part_id) for row in bom_items}
    for vehicle in vehicles[:2]:
        pair = (vehicle.id, parts[0].id)
        if pair not in existing_pairs:
            key = f"{vehicle.model_code}:{parts[0].part_number}:V1"
            bom_items.append(
                BOMItemModel(
                    **_base("bom", key),
                    vehicle_model_id=vehicle.id,
                    part_id=parts[0].id,
                    quantity=Decimal("1"),
                    bom_version="V1",
                    effective_from=date(2026, 1, 1),
                    effective_to=None,
                )
            )
    session.add_all(bom_items)

    supplier_parts = []
    for index, part in enumerate(parts):
        primary = suppliers[index % len(suppliers)]
        linked = [primary]
        if index < 15:
            linked.append(suppliers[(index + 1) % len(suppliers)])
        for supplier in linked:
            key = f"{supplier.supplier_code}:{part.part_number}"
            supplier_parts.append(
                SupplierPartModel(
                    **_base("supplier-part", key),
                    supplier_id=supplier.id,
                    part_id=part.id,
                    supplier_part_number=f"{supplier.supplier_code}-{part.part_number}",
                    lead_time_days=5 + (index % 12),
                    status=LifecycleStatus.ACTIVE,
                )
            )
    session.add_all(supplier_parts)

    plants = [
        PlantModel(
            **_base("plant", f"PLANT-{index:02d}"),
            plant_code=f"PLANT-{index:02d}",
            name=f"Synthetic Plant {index}",
            location=("North Campus", "Central Campus", "South Campus")[index - 1],
            status=LifecycleStatus.ACTIVE,
        )
        for index in range(1, 4)
    ]
    session.add_all(plants)

    processes = []
    process_types = ("RECEIVING", "ASSEMBLY", "FINAL_INSPECTION")
    for plant_index, plant in enumerate(plants, start=1):
        for process_index, process_type in enumerate(process_types, start=1):
            code = f"PROC-{plant_index}{process_index}"
            processes.append(
                ProcessModel(
                    **_base("process", code),
                    process_code=code,
                    name=f"{process_type.replace('_', ' ').title()} {plant_index}",
                    plant_id=plant.id,
                    process_type=process_type,
                    status=LifecycleStatus.ACTIVE,
                )
            )
    session.add_all(processes)

    batches = []
    for index in range(1, 37):
        number = f"BATCH-{index:03d}"
        manufactured = SEED_TIMESTAMP + timedelta(days=index)
        # First three batches intentionally share supplier SUP-001 for CASE-002.
        supplier = suppliers[0] if index <= 3 else suppliers[(index - 1) % len(suppliers)]
        part = parts[(index - 1) % len(parts)]
        batches.append(
            BatchModel(
                **_base("batch", number),
                batch_number=number,
                part_id=part.id,
                supplier_id=supplier.id,
                manufactured_at=manufactured,
                received_at=manufactured + timedelta(days=2),
                quantity=500 + index * 10,
                status=LifecycleStatus.ACTIVE,
            )
        )
    session.add_all(batches)

    inspections = []
    for batch_index, batch in enumerate(batches, start=1):
        for metric_index, metric_name in enumerate(("Width", "Torque", "Surface"), start=1):
            number = f"INSP-{batch_index:03d}-{metric_index}"
            lower = Decimal("9.50")
            upper = Decimal("10.50")
            # Explicit failures support CASE-001 and CASE-002; others add variety.
            fails = (batch_index in {1, 2, 3} and metric_index == 1) or (
                batch_index % 11 == 0 and metric_index == 2
            )
            measured = Decimal("10.80") if fails else Decimal("10.00")
            inspections.append(
                InspectionRecordModel(
                    **_base("inspection", number),
                    inspection_number=number,
                    batch_id=batch.id,
                    process_id=processes[(batch_index + metric_index) % len(processes)].id,
                    inspection_type="DIMENSIONAL" if metric_index == 1 else "PROCESS",
                    metric_name=metric_name,
                    measured_value=measured,
                    lower_limit=lower,
                    upper_limit=upper,
                    result=InspectionResult.FAIL if fails else InspectionResult.PASS,
                    inspected_at=batch.received_at + timedelta(hours=metric_index),
                )
            )
    session.add_all(inspections)

    issues = []
    for index in range(1, 17):
        number = f"ISSUE-{index:03d}"
        issues.append(
            QualityIssueModel(
                **_base("issue", number),
                issue_number=number,
                title=(
                    "Width above specification"
                    if index == 1
                    else f"Synthetic quality observation {index:02d}"
                ),
                description="Synthetic demonstration issue; no real manufacturer data.",
                severity=QualitySeverity.HIGH if index <= 3 else QualitySeverity.MEDIUM,
                status=QualityIssueStatus.INVESTIGATING if index <= 3 else QualityIssueStatus.OPEN,
                detected_at=SEED_TIMESTAMP + timedelta(days=index + 5),
                source="INSPECTION",
            )
        )
    session.add_all(issues)

    issue_batches = []
    for index, issue in enumerate(issues):
        linked_batches = [batches[index % len(batches)]]
        if index == 0:
            linked_batches = [batches[0]]
        elif index == 1:
            linked_batches = [batches[0], batches[1], batches[2]]
        elif index == 2:
            linked_batches = [batches[2], batches[3]]
        for batch in linked_batches:
            key = f"{issue.issue_number}:{batch.batch_number}"
            issue_batches.append(
                QualityIssueBatchModel(
                    **_base("issue-batch", key),
                    quality_issue_id=issue.id,
                    batch_id=batch.id,
                )
            )
    session.add_all(issue_batches)

    cases = []
    for index in range(1, 11):
        number = f"CASE-{index:03d}"
        cases.append(
            QualityCaseModel(
                **_base("case", number),
                case_number=number,
                title=(
                    "PART-001 dimensional investigation"
                    if index == 1
                    else f"Synthetic quality case {index:02d}"
                ),
                description="Synthetic case created for deterministic FactoryOps tests.",
                priority=CasePriority.HIGH if index <= 3 else CasePriority.MEDIUM,
                status=QualityCaseStatus.INVESTIGATING if index <= 3 else QualityCaseStatus.CLOSED,
                owner=f"quality.engineer{((index - 1) % 3) + 1}",
                opened_at=SEED_TIMESTAMP + timedelta(days=index + 7),
                closed_at=(
                    None
                    if index <= 3
                    else SEED_TIMESTAMP + timedelta(days=index + 20)
                ),
            )
        )
    session.add_all(cases)

    case_issues = []
    for index, case in enumerate(cases):
        linked = [issues[index]]
        if index == 0:
            linked.append(issues[1])
        for issue in linked:
            key = f"{case.case_number}:{issue.issue_number}"
            case_issues.append(
                QualityCaseIssueModel(
                    **_base("case-issue", key),
                    quality_case_id=case.id,
                    quality_issue_id=issue.id,
                )
            )
    session.add_all(case_issues)

    actions = []
    for index in range(1, 13):
        number = f"ACTION-{index:03d}"
        quality_case = cases[(index - 1) % len(cases)]
        actions.append(
            CorrectiveActionModel(
                **_base("action", number),
                action_number=number,
                quality_case_id=quality_case.id,
                title=f"Synthetic containment action {index:02d}",
                description="Review inspection fixture and confirm calibration using synthetic data.",
                action_type="CONTAINMENT" if index <= 3 else "CORRECTIVE",
                status=(
                    CorrectiveActionStatus.IN_PROGRESS
                    if index <= 3
                    else CorrectiveActionStatus.COMPLETED
                ),
                assignee=f"quality.engineer{((index - 1) % 3) + 1}",
                due_date=date(2026, 3, 1) + timedelta(days=index),
            )
        )
    session.add_all(actions)

    document_types = list(DocumentType)
    documents = []
    for index in range(1, 17):
        number = f"DOC-{index:03d}"
        documents.append(
            DocumentModel(
                **_base("document", number),
                document_number=number,
                title=f"Synthetic Manufacturing Guide {index:02d}",
                document_type=document_types[(index - 1) % len(document_types)],
                version="1.0",
                source_uri=f"synthetic://factoryops/documents/{number}.pdf",
                effective_from=date(2026, 1, 1),
                effective_to=None,
                status=LifecycleStatus.ACTIVE,
            )
        )
    session.add_all(documents)

    users = [
        UserModel(
            **_base("user", username),
            username=username,
            display_name=display_name,
            role=role,
            status=LifecycleStatus.ACTIVE,
        )
        for username, display_name, role in (
            ("quality.engineer1", "Synthetic Quality Engineer", UserRole.QUALITY_ENGINEER),
            ("supply.engineer1", "Synthetic Supply Engineer", UserRole.SUPPLY_ENGINEER),
            ("factoryops.admin", "Synthetic FactoryOps Admin", UserRole.ADMIN),
        )
    ]
    session.add_all(users)
    session.commit()

    counts = seed_counts(session)
    counts["status"] = "seeded"
    return counts


def seed_counts(session: Session) -> dict[str, int | str]:
    tables = {
        "suppliers": SupplierModel,
        "parts": PartModel,
        "vehicle_models": VehicleModelModel,
        "bom_items": BOMItemModel,
        "supplier_parts": SupplierPartModel,
        "plants": PlantModel,
        "processes": ProcessModel,
        "batches": BatchModel,
        "inspection_records": InspectionRecordModel,
        "quality_issues": QualityIssueModel,
        "quality_cases": QualityCaseModel,
        "corrective_actions": CorrectiveActionModel,
        "documents": DocumentModel,
        "users": UserModel,
    }
    return {
        name: int(session.scalar(select(func.count()).select_from(model)) or 0)
        for name, model in tables.items()
    }

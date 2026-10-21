"""Pure-Python FactoryOps entities.

The domain does not import FastAPI or SQLAlchemy. This keeps business services
reusable by REST endpoints, background jobs, and future Agent tools.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

from .enums import (
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
from .exceptions import DomainRuleViolation


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid4())


def _required(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise DomainRuleViolation(f"{field_name} is required", {"field": field_name})


@dataclass(slots=True)
class Entity:
    id: str = field(default_factory=new_id, kw_only=True)
    record_version: int = field(default=1, kw_only=True)
    created_at: datetime = field(default_factory=utc_now, kw_only=True)
    updated_at: datetime = field(default_factory=utc_now, kw_only=True)


@dataclass(slots=True)
class Supplier(Entity):
    supplier_code: str
    name: str
    category: str
    country: str
    status: LifecycleStatus = LifecycleStatus.ACTIVE
    risk_level: SupplierRiskLevel = SupplierRiskLevel.LOW

    def __post_init__(self) -> None:
        _required(self.supplier_code, "supplier_code")
        _required(self.name, "name")


@dataclass(slots=True)
class Part(Entity):
    part_number: str
    name: str
    category: str
    specification: str
    status: LifecycleStatus = LifecycleStatus.ACTIVE

    def __post_init__(self) -> None:
        _required(self.part_number, "part_number")
        _required(self.name, "name")


@dataclass(slots=True)
class VehicleModel(Entity):
    model_code: str
    name: str
    platform: str
    status: LifecycleStatus = LifecycleStatus.ACTIVE

    def __post_init__(self) -> None:
        _required(self.model_code, "model_code")
        _required(self.name, "name")


@dataclass(slots=True)
class BOMItem(Entity):
    vehicle_model_id: str
    part_id: str
    quantity: Decimal
    bom_version: str
    effective_from: date
    effective_to: date | None = None

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise DomainRuleViolation("BOM quantity must be positive")
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise DomainRuleViolation(
                "BOM effective_to must be on or after effective_from",
                {"effective_from": str(self.effective_from), "effective_to": str(self.effective_to)},
            )


@dataclass(slots=True)
class SupplierPart(Entity):
    supplier_id: str
    part_id: str
    supplier_part_number: str
    lead_time_days: int
    status: LifecycleStatus = LifecycleStatus.ACTIVE

    def __post_init__(self) -> None:
        _required(self.supplier_part_number, "supplier_part_number")
        if self.lead_time_days < 0:
            raise DomainRuleViolation("lead_time_days cannot be negative")


@dataclass(slots=True)
class Plant(Entity):
    plant_code: str
    name: str
    location: str
    status: LifecycleStatus = LifecycleStatus.ACTIVE

    def __post_init__(self) -> None:
        _required(self.plant_code, "plant_code")


@dataclass(slots=True)
class Process(Entity):
    process_code: str
    name: str
    plant_id: str
    process_type: str
    status: LifecycleStatus = LifecycleStatus.ACTIVE

    def __post_init__(self) -> None:
        _required(self.process_code, "process_code")


@dataclass(slots=True)
class Batch(Entity):
    batch_number: str
    part_id: str
    supplier_id: str
    manufactured_at: datetime
    received_at: datetime | None
    quantity: int
    status: LifecycleStatus = LifecycleStatus.ACTIVE

    def __post_init__(self) -> None:
        _required(self.batch_number, "batch_number")
        if self.quantity <= 0:
            raise DomainRuleViolation("Batch quantity must be positive")
        if self.received_at is not None and self.received_at < self.manufactured_at:
            raise DomainRuleViolation("received_at cannot precede manufactured_at")


@dataclass(slots=True)
class InspectionRecord(Entity):
    inspection_number: str
    batch_id: str
    process_id: str | None
    inspection_type: str
    metric_name: str
    measured_value: Decimal
    lower_limit: Decimal
    upper_limit: Decimal
    result: InspectionResult
    inspected_at: datetime

    def __post_init__(self) -> None:
        _required(self.inspection_number, "inspection_number")
        if self.lower_limit > self.upper_limit:
            raise DomainRuleViolation("lower_limit must not exceed upper_limit")
        expected = self.evaluate(self.measured_value, self.lower_limit, self.upper_limit)
        if self.result != expected:
            raise DomainRuleViolation(
                "Inspection result does not match measured value and limits",
                {"expected": expected.value, "actual": self.result.value},
            )

    @staticmethod
    def evaluate(value: Decimal, lower: Decimal, upper: Decimal) -> InspectionResult:
        if lower > upper:
            raise DomainRuleViolation("lower_limit must not exceed upper_limit")
        return InspectionResult.PASS if lower <= value <= upper else InspectionResult.FAIL

    @classmethod
    def create(
        cls,
        *,
        inspection_number: str,
        batch_id: str,
        process_id: str | None,
        inspection_type: str,
        metric_name: str,
        measured_value: Decimal,
        lower_limit: Decimal,
        upper_limit: Decimal,
        inspected_at: datetime,
    ) -> "InspectionRecord":
        return cls(
            inspection_number=inspection_number,
            batch_id=batch_id,
            process_id=process_id,
            inspection_type=inspection_type,
            metric_name=metric_name,
            measured_value=measured_value,
            lower_limit=lower_limit,
            upper_limit=upper_limit,
            result=cls.evaluate(measured_value, lower_limit, upper_limit),
            inspected_at=inspected_at,
        )


@dataclass(slots=True)
class QualityIssue(Entity):
    issue_number: str
    title: str
    description: str
    severity: QualitySeverity
    status: QualityIssueStatus
    detected_at: datetime
    source: str

    def __post_init__(self) -> None:
        _required(self.issue_number, "issue_number")
        _required(self.title, "title")


@dataclass(slots=True)
class QualityCase(Entity):
    case_number: str
    title: str
    description: str
    priority: CasePriority
    status: QualityCaseStatus
    owner: str
    opened_at: datetime
    closed_at: datetime | None = None

    def __post_init__(self) -> None:
        _required(self.case_number, "case_number")
        _required(self.title, "title")
        if self.closed_at is not None and self.closed_at < self.opened_at:
            raise DomainRuleViolation("closed_at cannot precede opened_at")


@dataclass(slots=True)
class CorrectiveAction(Entity):
    action_number: str
    quality_case_id: str
    title: str
    description: str
    action_type: str
    status: CorrectiveActionStatus
    assignee: str
    due_date: date

    def __post_init__(self) -> None:
        _required(self.action_number, "action_number")
        _required(self.title, "title")


@dataclass(slots=True)
class Document(Entity):
    document_number: str
    title: str
    document_type: DocumentType
    version: str
    source_uri: str
    effective_from: date
    effective_to: date | None
    status: LifecycleStatus = LifecycleStatus.ACTIVE

    def __post_init__(self) -> None:
        _required(self.document_number, "document_number")
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise DomainRuleViolation("Document effective_to must not precede effective_from")


@dataclass(slots=True)
class User(Entity):
    username: str
    display_name: str
    role: UserRole
    status: LifecycleStatus = LifecycleStatus.ACTIVE

    def __post_init__(self) -> None:
        _required(self.username, "username")

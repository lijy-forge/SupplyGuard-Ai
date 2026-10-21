"""Versioned API contracts; ORM models never cross this boundary."""

from datetime import date, datetime
from decimal import Decimal
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from factoryops.domain.enums import (
    CasePriority,
    CorrectiveActionStatus,
    InspectionResult,
    LifecycleStatus,
    QualityCaseStatus,
    QualityIssueStatus,
    QualitySeverity,
    SupplierRiskLevel,
)

T = TypeVar("T")


class DataResponse(BaseModel, Generic[T]):
    data: T


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorBody


class EntityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    record_version: int
    created_at: datetime
    updated_at: datetime


class SupplierRead(EntityRead):
    supplier_code: str
    name: str
    category: str
    country: str
    status: LifecycleStatus
    risk_level: SupplierRiskLevel


class PartRead(EntityRead):
    part_number: str
    name: str
    category: str
    specification: str
    status: LifecycleStatus


class VehicleModelRead(EntityRead):
    model_code: str
    name: str
    platform: str
    status: LifecycleStatus


class BatchRead(EntityRead):
    batch_number: str
    part_id: str
    supplier_id: str
    manufactured_at: datetime
    received_at: datetime | None
    quantity: int
    status: LifecycleStatus


class InspectionRead(EntityRead):
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


class QualityIssueRead(EntityRead):
    issue_number: str
    title: str
    description: str
    severity: QualitySeverity
    status: QualityIssueStatus
    detected_at: datetime
    source: str


class QualityCaseRead(EntityRead):
    case_number: str
    title: str
    description: str
    priority: CasePriority
    status: QualityCaseStatus
    owner: str
    opened_at: datetime
    closed_at: datetime | None


class CorrectiveActionRead(EntityRead):
    action_number: str
    quality_case_id: str
    title: str
    description: str
    action_type: str
    status: CorrectiveActionStatus
    assignee: str
    due_date: date


class SupplierDetail(BaseModel):
    supplier: SupplierRead
    parts: list[PartRead]


class VehicleImpactRead(BaseModel):
    vehicle_model: VehicleModelRead
    bom_versions: list[str]


class PartDetail(BaseModel):
    part: PartRead
    suppliers: list[SupplierRead]
    vehicle_models: list[VehicleImpactRead]


class InspectionSummaryRead(BaseModel):
    total: int
    passed: int
    failed: int
    records: list[InspectionRead]


class BatchContextRead(BaseModel):
    batch: BatchRead
    part: PartRead
    supplier: SupplierRead
    inspection_summary: InspectionSummaryRead
    related_quality_issues: list[QualityIssueRead]


class PartVehicleImpactRead(BaseModel):
    part: PartRead
    vehicle_models: list[VehicleImpactRead]


class QualityCaseDetailRead(BaseModel):
    quality_case: QualityCaseRead
    issues: list[QualityIssueRead]
    corrective_actions: list[CorrectiveActionRead]


class QualityCaseCreate(BaseModel):
    case_number: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=250)
    description: str = Field(min_length=1)
    priority: CasePriority
    status: QualityCaseStatus = QualityCaseStatus.OPEN
    owner: str = Field(min_length=1, max_length=120)
    opened_at: datetime


class CorrectiveActionCreate(BaseModel):
    action_number: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=250)
    description: str = Field(min_length=1)
    action_type: str = Field(min_length=1, max_length=100)
    status: CorrectiveActionStatus = CorrectiveActionStatus.OPEN
    assignee: str = Field(min_length=1, max_length=120)
    due_date: date


class InspectionCreate(BaseModel):
    inspection_number: str = Field(min_length=1, max_length=80)
    process_id: str | None = None
    inspection_type: str = Field(min_length=1, max_length=100)
    metric_name: str = Field(min_length=1, max_length=100)
    measured_value: Decimal
    lower_limit: Decimal
    upper_limit: Decimal
    inspected_at: datetime


class HealthRead(BaseModel):
    status: str
    service: str
    version: str
    database: str

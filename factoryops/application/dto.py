"""Transport-neutral application result objects."""

from dataclasses import dataclass

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


@dataclass(frozen=True, slots=True)
class InspectionSummary:
    total: int
    passed: int
    failed: int
    records: tuple[InspectionRecord, ...]


@dataclass(frozen=True, slots=True)
class BatchContext:
    batch: Batch
    part: Part
    supplier: Supplier
    inspection_summary: InspectionSummary
    related_quality_issues: tuple[QualityIssue, ...]


@dataclass(frozen=True, slots=True)
class VehicleImpact:
    vehicle_model: VehicleModel
    bom_versions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PartVehicleImpact:
    part: Part
    vehicle_models: tuple[VehicleImpact, ...]


@dataclass(frozen=True, slots=True)
class QualityCaseDetail:
    quality_case: QualityCase
    issues: tuple[QualityIssue, ...]
    corrective_actions: tuple[CorrectiveAction, ...]

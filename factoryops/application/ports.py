"""Repository and transaction ports owned by the application layer."""

from __future__ import annotations

from abc import ABC, abstractmethod
from types import TracebackType

from factoryops.domain.entities import (
    Batch,
    CorrectiveAction,
    InspectionRecord,
    Part,
    QualityCase,
    QualityIssue,
    Supplier,
)

from .dto import BatchContext, PartVehicleImpact, QualityCaseDetail


class SupplierRepository(ABC):
    @abstractmethod
    def list(self) -> list[Supplier]: ...

    @abstractmethod
    def get_by_code(self, supplier_code: str) -> Supplier | None: ...

    @abstractmethod
    def get_parts(self, supplier_id: str) -> list[Part]: ...


class PartRepository(ABC):
    @abstractmethod
    def list(self) -> list[Part]: ...

    @abstractmethod
    def get_by_number(self, part_number: str) -> Part | None: ...

    @abstractmethod
    def get_suppliers(self, part_id: str) -> list[Supplier]: ...

    @abstractmethod
    def get_vehicle_impact(self, part_number: str) -> PartVehicleImpact | None: ...


class BatchRepository(ABC):
    @abstractmethod
    def get_by_number(self, batch_number: str) -> Batch | None: ...

    @abstractmethod
    def get_context(self, batch_number: str) -> BatchContext | None: ...


class InspectionRepository(ABC):
    @abstractmethod
    def add(self, inspection: InspectionRecord) -> InspectionRecord: ...

    @abstractmethod
    def list_for_batch(self, batch_id: str) -> list[InspectionRecord]: ...


class QualityCaseRepository(ABC):
    @abstractmethod
    def add(self, quality_case: QualityCase) -> QualityCase: ...

    @abstractmethod
    def list(self) -> list[QualityCase]: ...

    @abstractmethod
    def get_by_number(self, case_number: str) -> QualityCaseDetail | None: ...

    @abstractmethod
    def find_issue(self, issue_number: str) -> QualityIssue | None: ...

    @abstractmethod
    def associate_issue(self, quality_case_id: str, quality_issue_id: str) -> None: ...

    @abstractmethod
    def add_action(self, action: CorrectiveAction) -> CorrectiveAction: ...


class AbstractUnitOfWork(ABC):
    suppliers: SupplierRepository
    parts: PartRepository
    batches: BatchRepository
    inspections: InspectionRepository
    quality_cases: QualityCaseRepository

    @abstractmethod
    def __enter__(self) -> "AbstractUnitOfWork": ...

    @abstractmethod
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...

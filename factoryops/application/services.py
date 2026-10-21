"""FactoryOps use cases.

No service imports SQLAlchemy or FastAPI. The same calls can later be wrapped
as Agent tools without granting a tool direct database access.
"""

from collections.abc import Callable

from factoryops.domain.entities import CorrectiveAction, InspectionRecord, QualityCase
from factoryops.domain.exceptions import NotFoundError

from .dto import BatchContext, InspectionSummary, PartVehicleImpact, QualityCaseDetail
from .ports import AbstractUnitOfWork

UowFactory = Callable[[], AbstractUnitOfWork]


class SupplierService:
    def __init__(self, uow_factory: UowFactory) -> None:
        self._uow_factory = uow_factory

    def list_suppliers(self):
        with self._uow_factory() as uow:
            return uow.suppliers.list()

    def get_supplier(self, supplier_code: str):
        with self._uow_factory() as uow:
            supplier = uow.suppliers.get_by_code(supplier_code)
            if supplier is None:
                raise NotFoundError(
                    f"Supplier {supplier_code} was not found",
                    {"supplier_code": supplier_code, "entity": "supplier"},
                )
            return supplier

    def get_supplier_parts(self, supplier_code: str):
        with self._uow_factory() as uow:
            supplier = uow.suppliers.get_by_code(supplier_code)
            if supplier is None:
                raise NotFoundError(f"Supplier {supplier_code} was not found")
            return uow.suppliers.get_parts(supplier.id)


class PartService:
    def __init__(self, uow_factory: UowFactory) -> None:
        self._uow_factory = uow_factory

    def list_parts(self):
        with self._uow_factory() as uow:
            return uow.parts.list()

    def get_part(self, part_number: str):
        with self._uow_factory() as uow:
            part = uow.parts.get_by_number(part_number)
            if part is None:
                raise NotFoundError(
                    f"Part {part_number} was not found",
                    {"part_number": part_number, "entity": "part"},
                )
            return part

    def get_part_suppliers(self, part_number: str):
        with self._uow_factory() as uow:
            part = uow.parts.get_by_number(part_number)
            if part is None:
                raise NotFoundError(f"Part {part_number} was not found")
            return uow.parts.get_suppliers(part.id)

    def get_part_vehicle_models(self, part_number: str):
        return self.get_part_vehicle_impact(part_number).vehicle_models

    def get_part_vehicle_impact(self, part_number: str) -> PartVehicleImpact:
        with self._uow_factory() as uow:
            impact = uow.parts.get_vehicle_impact(part_number)
            if impact is None:
                raise NotFoundError(
                    f"Part {part_number} was not found",
                    {"part_number": part_number, "entity": "part"},
                )
            return impact


class BatchService:
    def __init__(self, uow_factory: UowFactory) -> None:
        self._uow_factory = uow_factory

    def get_batch(self, batch_number: str):
        with self._uow_factory() as uow:
            batch = uow.batches.get_by_number(batch_number)
            if batch is None:
                raise NotFoundError(
                    f"Batch {batch_number} was not found",
                    {"batch_number": batch_number, "entity": "batch"},
                )
            return batch

    def get_batch_context(self, batch_number: str) -> BatchContext:
        with self._uow_factory() as uow:
            context = uow.batches.get_context(batch_number)
            if context is None:
                raise NotFoundError(
                    f"Batch {batch_number} was not found",
                    {"batch_number": batch_number, "entity": "batch"},
                )
            return context


class InspectionService:
    def __init__(self, uow_factory: UowFactory) -> None:
        self._uow_factory = uow_factory

    def create_inspection_record(self, inspection: InspectionRecord) -> InspectionRecord:
        with self._uow_factory() as uow:
            created = uow.inspections.add(inspection)
            uow.commit()
            return created

    def list_batch_inspections(self, batch_number: str):
        with self._uow_factory() as uow:
            batch = uow.batches.get_by_number(batch_number)
            if batch is None:
                raise NotFoundError(f"Batch {batch_number} was not found")
            return uow.inspections.list_for_batch(batch.id)

    def summarize_batch_inspections(self, batch_number: str) -> InspectionSummary:
        records = self.list_batch_inspections(batch_number)
        passed = sum(item.result.value == "PASS" for item in records)
        return InspectionSummary(
            total=len(records),
            passed=passed,
            failed=len(records) - passed,
            records=tuple(records),
        )


class QualityService:
    def __init__(self, uow_factory: UowFactory) -> None:
        self._uow_factory = uow_factory

    def create_quality_case(self, quality_case: QualityCase) -> QualityCase:
        with self._uow_factory() as uow:
            created = uow.quality_cases.add(quality_case)
            uow.commit()
            return created

    def list_quality_cases(self):
        with self._uow_factory() as uow:
            return uow.quality_cases.list()

    def get_quality_case(self, case_number: str) -> QualityCaseDetail:
        with self._uow_factory() as uow:
            detail = uow.quality_cases.get_by_number(case_number)
            if detail is None:
                raise NotFoundError(
                    f"Quality case {case_number} was not found",
                    {"case_number": case_number, "entity": "quality_case"},
                )
            return detail

    def add_issue_to_case(self, case_number: str, issue_number: str) -> QualityCaseDetail:
        with self._uow_factory() as uow:
            detail = uow.quality_cases.get_by_number(case_number)
            if detail is None:
                raise NotFoundError(f"Quality case {case_number} was not found")
            issue = uow.quality_cases.find_issue(issue_number)
            if issue is None:
                raise NotFoundError(f"Quality issue {issue_number} was not found")
            uow.quality_cases.associate_issue(detail.quality_case.id, issue.id)
            uow.commit()
        return self.get_quality_case(case_number)

    def create_corrective_action(
        self, case_number: str, action: CorrectiveAction
    ) -> CorrectiveAction:
        with self._uow_factory() as uow:
            detail = uow.quality_cases.get_by_number(case_number)
            if detail is None:
                raise NotFoundError(f"Quality case {case_number} was not found")
            if action.quality_case_id != detail.quality_case.id:
                action.quality_case_id = detail.quality_case.id
            created = uow.quality_cases.add_action(action)
            uow.commit()
            return created

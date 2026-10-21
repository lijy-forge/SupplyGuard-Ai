from datetime import date, datetime, timezone

import pytest

from factoryops.application.services import BatchService, PartService, QualityService, SupplierService
from factoryops.domain.entities import CorrectiveAction, QualityCase
from factoryops.domain.enums import (
    CasePriority,
    CorrectiveActionStatus,
    QualityCaseStatus,
)
from factoryops.domain.exceptions import NotFoundError


def test_supplier_and_supplier_parts(uow_factory):
    service = SupplierService(uow_factory)
    assert len(service.list_suppliers()) == 10
    assert service.get_supplier("SUP-001").name.startswith("Synthetic")
    assert service.get_supplier_parts("SUP-001")


def test_missing_supplier_is_stable_not_found(uow_factory):
    with pytest.raises(NotFoundError) as exc:
        SupplierService(uow_factory).get_supplier("MISSING")
    assert exc.value.code == "NOT_FOUND"


def test_batch_context_contains_failures_and_issues(uow_factory):
    context = BatchService(uow_factory).get_batch_context("BATCH-001")
    assert context.part.part_number == "PART-001"
    assert context.supplier.supplier_code == "SUP-001"
    assert context.inspection_summary.failed >= 1
    assert context.related_quality_issues


def test_part_vehicle_impact_is_sql_baseline(uow_factory):
    impact = PartService(uow_factory).get_part_vehicle_impact("PART-001")
    codes = {item.vehicle_model.model_code for item in impact.vehicle_models}
    assert {"VM-A", "VM-B"}.issubset(codes)
    assert all(item.bom_versions for item in impact.vehicle_models)


def test_create_quality_case(uow_factory):
    service = QualityService(uow_factory)
    created = service.create_quality_case(
        QualityCase(
            case_number="CASE-NEW",
            title="New synthetic case",
            description="Test",
            priority=CasePriority.MEDIUM,
            status=QualityCaseStatus.OPEN,
            owner="quality.engineer1",
            opened_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
        )
    )
    assert service.get_quality_case(created.case_number).quality_case.id == created.id


def test_associate_issue_to_case(uow_factory):
    detail = QualityService(uow_factory).add_issue_to_case("CASE-003", "ISSUE-004")
    assert "ISSUE-004" in {issue.issue_number for issue in detail.issues}


def test_create_corrective_action(uow_factory):
    service = QualityService(uow_factory)
    case = service.get_quality_case("CASE-001").quality_case
    action = service.create_corrective_action(
        "CASE-001",
        CorrectiveAction(
            action_number="ACTION-NEW",
            quality_case_id=case.id,
            title="Verify synthetic gauge",
            description="Deterministic test action",
            action_type="CORRECTIVE",
            status=CorrectiveActionStatus.OPEN,
            assignee="quality.engineer1",
            due_date=date(2026, 5, 1),
        ),
    )
    assert action.action_number == "ACTION-NEW"
    assert any(
        item.action_number == "ACTION-NEW"
        for item in service.get_quality_case("CASE-001").corrective_actions
    )

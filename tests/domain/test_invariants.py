from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from factoryops.domain.entities import BOMItem, Batch, InspectionRecord, QualityCase
from factoryops.domain.enums import CasePriority, InspectionResult, QualityCaseStatus
from factoryops.domain.exceptions import DomainRuleViolation

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_inspection_inside_limits_is_pass():
    record = InspectionRecord.create(
        inspection_number="I-1",
        batch_id="batch",
        process_id=None,
        inspection_type="DIMENSIONAL",
        metric_name="Width",
        measured_value=Decimal("10.0"),
        lower_limit=Decimal("9.5"),
        upper_limit=Decimal("10.5"),
        inspected_at=NOW,
    )
    assert record.result is InspectionResult.PASS


@pytest.mark.parametrize("value", [Decimal("9.49"), Decimal("10.51")])
def test_inspection_outside_limits_is_fail(value):
    record = InspectionRecord.create(
        inspection_number="I-2",
        batch_id="batch",
        process_id=None,
        inspection_type="DIMENSIONAL",
        metric_name="Width",
        measured_value=value,
        lower_limit=Decimal("9.5"),
        upper_limit=Decimal("10.5"),
        inspected_at=NOW,
    )
    assert record.result is InspectionResult.FAIL


def test_inspection_rejects_inverted_limits():
    with pytest.raises(DomainRuleViolation):
        InspectionRecord.create(
            inspection_number="I-3",
            batch_id="batch",
            process_id=None,
            inspection_type="DIMENSIONAL",
            metric_name="Width",
            measured_value=Decimal("10"),
            lower_limit=Decimal("11"),
            upper_limit=Decimal("9"),
            inspected_at=NOW,
        )


def test_inspection_rejects_inconsistent_explicit_result():
    with pytest.raises(DomainRuleViolation):
        InspectionRecord(
            inspection_number="I-4",
            batch_id="batch",
            process_id=None,
            inspection_type="DIMENSIONAL",
            metric_name="Width",
            measured_value=Decimal("12"),
            lower_limit=Decimal("9"),
            upper_limit=Decimal("11"),
            result=InspectionResult.PASS,
            inspected_at=NOW,
        )


def test_bom_rejects_invalid_effectivity():
    with pytest.raises(DomainRuleViolation):
        BOMItem(
            vehicle_model_id="vehicle",
            part_id="part",
            quantity=Decimal("1"),
            bom_version="V1",
            effective_from=date(2026, 2, 1),
            effective_to=date(2026, 1, 1),
        )


def test_bom_rejects_nonpositive_quantity():
    with pytest.raises(DomainRuleViolation):
        BOMItem(
            vehicle_model_id="vehicle",
            part_id="part",
            quantity=Decimal("0"),
            bom_version="V1",
            effective_from=date(2026, 1, 1),
        )


def test_batch_rejects_received_before_manufactured():
    with pytest.raises(DomainRuleViolation):
        Batch(
            batch_number="B-1",
            part_id="part",
            supplier_id="supplier",
            manufactured_at=NOW,
            received_at=NOW - timedelta(days=1),
            quantity=1,
        )


def test_quality_case_rejects_closed_before_opened():
    with pytest.raises(DomainRuleViolation):
        QualityCase(
            case_number="C-1",
            title="Case",
            description="Description",
            priority=CasePriority.HIGH,
            status=QualityCaseStatus.CLOSED,
            owner="owner",
            opened_at=NOW,
            closed_at=NOW - timedelta(days=1),
        )

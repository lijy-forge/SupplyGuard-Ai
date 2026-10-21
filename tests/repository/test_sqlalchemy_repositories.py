from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select

from factoryops.application.services import QualityService
from factoryops.domain.entities import QualityCase
from factoryops.domain.enums import CasePriority, QualityCaseStatus
from factoryops.domain.exceptions import ConflictError
from factoryops.infrastructure.db.models import (
    BatchModel,
    CorrectiveActionModel,
    PartModel,
    QualityCaseModel,
    QualityIssueBatchModel,
    QualityIssueModel,
    SupplierModel,
    VehicleModelModel,
)


def test_unique_case_number_maps_to_conflict(uow_factory):
    service = QualityService(uow_factory)
    duplicate = QualityCase(
        case_number="CASE-001",
        title="Duplicate",
        description="Must fail",
        priority=CasePriority.LOW,
        status=QualityCaseStatus.OPEN,
        owner="quality.engineer1",
        opened_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
    )
    with pytest.raises(ConflictError):
        service.create_quality_case(duplicate)


def test_part_supports_multiple_suppliers(uow_factory):
    with uow_factory() as uow:
        part = uow.parts.get_by_number("PART-001")
        suppliers = uow.parts.get_suppliers(part.id)
    assert len(suppliers) == 2


def test_quality_issue_can_affect_multiple_batches(session_factory):
    with session_factory() as session:
        counts = session.scalars(
            select(func.count())
            .select_from(QualityIssueBatchModel)
            .group_by(QualityIssueBatchModel.quality_issue_id)
        ).all()
        max_links = max(counts)
    assert max_links >= 3


def test_seed_is_idempotent(session_factory):
    from factoryops.infrastructure.db.seed import seed_database

    with session_factory() as session:
        result = seed_database(session)
    assert result["status"] == "already_seeded"
    assert result["inspection_records"] == 108


@pytest.mark.parametrize(
    ("model", "column_name"),
    [
        (SupplierModel, "supplier_code"),
        (PartModel, "part_number"),
        (VehicleModelModel, "model_code"),
        (BatchModel, "batch_number"),
        (QualityIssueModel, "issue_number"),
        (QualityCaseModel, "case_number"),
        (CorrectiveActionModel, "action_number"),
    ],
)
def test_required_business_keys_are_unique_in_schema(model, column_name):
    assert model.__table__.columns[column_name].unique is True


def test_record_version_increments_on_update(session_factory):
    with session_factory() as session:
        supplier = session.query(SupplierModel).filter_by(supplier_code="SUP-001").one()
        assert supplier.record_version == 1
        supplier.name = "Updated Synthetic Components"
        session.commit()
        assert supplier.record_version == 2

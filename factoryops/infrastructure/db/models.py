"""FactoryOps relational schema.

The schema deliberately uses portable SQLAlchemy types for Level B tests while
PostgreSQL remains the production system of record.
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

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

from .base import Base, EntityMixin


def enum_type(enum_class, name: str) -> Enum:
    return Enum(
        enum_class,
        name=name,
        native_enum=False,
        create_constraint=True,
        validate_strings=True,
        values_callable=lambda members: [member.value for member in members],
    )


class SupplierModel(EntityMixin, Base):
    __tablename__ = "fo_suppliers"

    supplier_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[LifecycleStatus] = mapped_column(
        enum_type(LifecycleStatus, "supplier_status"), nullable=False
    )
    risk_level: Mapped[SupplierRiskLevel] = mapped_column(
        enum_type(SupplierRiskLevel, "supplier_risk_level"), nullable=False
    )


class PartModel(EntityMixin, Base):
    __tablename__ = "fo_parts"

    part_number: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    specification: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[LifecycleStatus] = mapped_column(
        enum_type(LifecycleStatus, "part_status"), nullable=False
    )


class VehicleModelModel(EntityMixin, Base):
    __tablename__ = "fo_vehicle_models"

    model_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    platform: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[LifecycleStatus] = mapped_column(
        enum_type(LifecycleStatus, "vehicle_model_status"), nullable=False
    )


class BOMItemModel(EntityMixin, Base):
    __tablename__ = "fo_bom_items"
    __table_args__ = (
        UniqueConstraint(
            "vehicle_model_id", "part_id", "bom_version", "effective_from",
            name="uq_fo_bom_item_effectivity",
        ),
        CheckConstraint("quantity > 0", name="ck_fo_bom_quantity_positive"),
        CheckConstraint(
            "effective_to IS NULL OR effective_to >= effective_from",
            name="ck_fo_bom_effective_dates",
        ),
    )

    vehicle_model_id: Mapped[str] = mapped_column(
        ForeignKey("fo_vehicle_models.id", ondelete="CASCADE"), nullable=False
    )
    part_id: Mapped[str] = mapped_column(
        ForeignKey("fo_parts.id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    bom_version: Mapped[str] = mapped_column(String(40), nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)


class SupplierPartModel(EntityMixin, Base):
    __tablename__ = "fo_supplier_parts"
    __table_args__ = (
        UniqueConstraint("supplier_id", "part_id", name="uq_fo_supplier_part"),
        UniqueConstraint(
            "supplier_id", "supplier_part_number", name="uq_fo_supplier_part_number"
        ),
        CheckConstraint("lead_time_days >= 0", name="ck_fo_lead_time_nonnegative"),
    )

    supplier_id: Mapped[str] = mapped_column(
        ForeignKey("fo_suppliers.id", ondelete="CASCADE"), nullable=False
    )
    part_id: Mapped[str] = mapped_column(
        ForeignKey("fo_parts.id", ondelete="CASCADE"), nullable=False
    )
    supplier_part_number: Mapped[str] = mapped_column(String(100), nullable=False)
    lead_time_days: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[LifecycleStatus] = mapped_column(
        enum_type(LifecycleStatus, "supplier_part_status"), nullable=False
    )


class PlantModel(EntityMixin, Base):
    __tablename__ = "fo_plants"

    plant_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[LifecycleStatus] = mapped_column(
        enum_type(LifecycleStatus, "plant_status"), nullable=False
    )


class ProcessModel(EntityMixin, Base):
    __tablename__ = "fo_processes"

    process_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    plant_id: Mapped[str] = mapped_column(
        ForeignKey("fo_plants.id", ondelete="RESTRICT"), nullable=False
    )
    process_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[LifecycleStatus] = mapped_column(
        enum_type(LifecycleStatus, "process_status"), nullable=False
    )


class BatchModel(EntityMixin, Base):
    __tablename__ = "fo_batches"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_fo_batch_quantity_positive"),
        CheckConstraint(
            "received_at IS NULL OR received_at >= manufactured_at",
            name="ck_fo_batch_received_after_manufactured",
        ),
        Index("ix_fo_batches_part_supplier", "part_id", "supplier_id"),
    )

    batch_number: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    part_id: Mapped[str] = mapped_column(
        ForeignKey("fo_parts.id", ondelete="RESTRICT"), nullable=False
    )
    supplier_id: Mapped[str] = mapped_column(
        ForeignKey("fo_suppliers.id", ondelete="RESTRICT"), nullable=False
    )
    manufactured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[LifecycleStatus] = mapped_column(
        enum_type(LifecycleStatus, "batch_status"), nullable=False
    )


class InspectionRecordModel(EntityMixin, Base):
    __tablename__ = "fo_inspection_records"
    __table_args__ = (
        CheckConstraint("lower_limit <= upper_limit", name="ck_fo_inspection_limits"),
        Index("ix_fo_inspections_batch_result", "batch_id", "result"),
    )

    inspection_number: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    batch_id: Mapped[str] = mapped_column(
        ForeignKey("fo_batches.id", ondelete="CASCADE"), nullable=False
    )
    process_id: Mapped[str | None] = mapped_column(
        ForeignKey("fo_processes.id", ondelete="SET NULL"), nullable=True
    )
    inspection_type: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    measured_value: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    lower_limit: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    upper_limit: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    result: Mapped[InspectionResult] = mapped_column(
        enum_type(InspectionResult, "inspection_result"), nullable=False
    )
    inspected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class QualityIssueModel(EntityMixin, Base):
    __tablename__ = "fo_quality_issues"

    issue_number: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[QualitySeverity] = mapped_column(
        enum_type(QualitySeverity, "quality_severity"), nullable=False
    )
    status: Mapped[QualityIssueStatus] = mapped_column(
        enum_type(QualityIssueStatus, "quality_issue_status"), nullable=False
    )
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(120), nullable=False)


class QualityIssueBatchModel(EntityMixin, Base):
    __tablename__ = "fo_quality_issue_batches"
    __table_args__ = (
        UniqueConstraint("quality_issue_id", "batch_id", name="uq_fo_issue_batch"),
    )

    quality_issue_id: Mapped[str] = mapped_column(
        ForeignKey("fo_quality_issues.id", ondelete="CASCADE"), nullable=False
    )
    batch_id: Mapped[str] = mapped_column(
        ForeignKey("fo_batches.id", ondelete="CASCADE"), nullable=False
    )


class QualityCaseModel(EntityMixin, Base):
    __tablename__ = "fo_quality_cases"
    __table_args__ = (
        CheckConstraint(
            "closed_at IS NULL OR closed_at >= opened_at", name="ck_fo_case_closed_after_opened"
        ),
    )

    case_number: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[CasePriority] = mapped_column(
        enum_type(CasePriority, "quality_case_priority"), nullable=False
    )
    status: Mapped[QualityCaseStatus] = mapped_column(
        enum_type(QualityCaseStatus, "quality_case_status"), nullable=False
    )
    owner: Mapped[str] = mapped_column(String(120), nullable=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class QualityCaseIssueModel(EntityMixin, Base):
    __tablename__ = "fo_quality_case_issues"
    __table_args__ = (
        UniqueConstraint("quality_case_id", "quality_issue_id", name="uq_fo_case_issue"),
    )

    quality_case_id: Mapped[str] = mapped_column(
        ForeignKey("fo_quality_cases.id", ondelete="CASCADE"), nullable=False
    )
    quality_issue_id: Mapped[str] = mapped_column(
        ForeignKey("fo_quality_issues.id", ondelete="CASCADE"), nullable=False
    )


class CorrectiveActionModel(EntityMixin, Base):
    __tablename__ = "fo_corrective_actions"

    action_number: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    quality_case_id: Mapped[str] = mapped_column(
        ForeignKey("fo_quality_cases.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[CorrectiveActionStatus] = mapped_column(
        enum_type(CorrectiveActionStatus, "corrective_action_status"), nullable=False
    )
    assignee: Mapped[str] = mapped_column(String(120), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)


class DocumentModel(EntityMixin, Base):
    __tablename__ = "fo_documents"
    __table_args__ = (
        UniqueConstraint("document_number", "version", name="uq_fo_document_version"),
        CheckConstraint(
            "effective_to IS NULL OR effective_to >= effective_from",
            name="ck_fo_document_effective_dates",
        ),
    )

    document_number: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    document_type: Mapped[DocumentType] = mapped_column(
        enum_type(DocumentType, "document_type"), nullable=False
    )
    version: Mapped[str] = mapped_column(String(40), nullable=False)
    source_uri: Mapped[str] = mapped_column(String(500), nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date)
    status: Mapped[LifecycleStatus] = mapped_column(
        enum_type(LifecycleStatus, "document_status"), nullable=False
    )


class UserModel(EntityMixin, Base):
    __tablename__ = "fo_users"

    username: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[UserRole] = mapped_column(enum_type(UserRole, "user_role"), nullable=False)
    status: Mapped[LifecycleStatus] = mapped_column(
        enum_type(LifecycleStatus, "user_status"), nullable=False
    )

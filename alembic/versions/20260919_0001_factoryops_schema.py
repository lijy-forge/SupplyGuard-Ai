"""Create the initial FactoryOps manufacturing-quality schema.

Revision ID: 20260919_0001
Revises: None
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260919_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def entity_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("record_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    ]


def enum_type(name: str, values: tuple[str, ...]) -> sa.Enum:
    return sa.Enum(*values, name=name, native_enum=False, create_constraint=True)


def upgrade() -> None:
    lifecycle = ("ACTIVE", "INACTIVE")
    op.create_table(
        "fo_suppliers",
        *entity_columns(),
        sa.Column("supplier_code", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("country", sa.String(100), nullable=False),
        sa.Column("status", enum_type("supplier_status", lifecycle), nullable=False),
        sa.Column("risk_level", enum_type("supplier_risk_level", ("LOW", "MEDIUM", "HIGH")), nullable=False),
    )
    op.create_table(
        "fo_parts",
        *entity_columns(),
        sa.Column("part_number", sa.String(80), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("specification", sa.Text(), nullable=False),
        sa.Column("status", enum_type("part_status", lifecycle), nullable=False),
    )
    op.create_table(
        "fo_vehicle_models",
        *entity_columns(),
        sa.Column("model_code", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("platform", sa.String(100), nullable=False),
        sa.Column("status", enum_type("vehicle_model_status", lifecycle), nullable=False),
    )
    op.create_table(
        "fo_plants",
        *entity_columns(),
        sa.Column("plant_code", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("location", sa.String(200), nullable=False),
        sa.Column("status", enum_type("plant_status", lifecycle), nullable=False),
    )
    op.create_table(
        "fo_documents",
        *entity_columns(),
        sa.Column("document_number", sa.String(80), nullable=False),
        sa.Column("title", sa.String(250), nullable=False),
        sa.Column("document_type", enum_type("document_type", ("SOP", "FMEA", "8D", "QUALITY_STANDARD", "INSPECTION_GUIDE", "OTHER")), nullable=False),
        sa.Column("version", sa.String(40), nullable=False),
        sa.Column("source_uri", sa.String(500), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date()),
        sa.Column("status", enum_type("document_status", lifecycle), nullable=False),
        sa.UniqueConstraint("document_number", "version", name="uq_fo_document_version"),
        sa.CheckConstraint("effective_to IS NULL OR effective_to >= effective_from", name="ck_fo_document_effective_dates"),
    )
    op.create_table(
        "fo_users",
        *entity_columns(),
        sa.Column("username", sa.String(80), nullable=False, unique=True),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("role", enum_type("user_role", ("VIEWER", "QUALITY_ENGINEER", "SUPPLY_ENGINEER", "ADMIN")), nullable=False),
        sa.Column("status", enum_type("user_status", lifecycle), nullable=False),
    )
    op.create_table(
        "fo_processes",
        *entity_columns(),
        sa.Column("process_code", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("plant_id", sa.String(36), sa.ForeignKey("fo_plants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("process_type", sa.String(100), nullable=False),
        sa.Column("status", enum_type("process_status", lifecycle), nullable=False),
    )
    op.create_table(
        "fo_supplier_parts",
        *entity_columns(),
        sa.Column("supplier_id", sa.String(36), sa.ForeignKey("fo_suppliers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("part_id", sa.String(36), sa.ForeignKey("fo_parts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("supplier_part_number", sa.String(100), nullable=False),
        sa.Column("lead_time_days", sa.Integer(), nullable=False),
        sa.Column("status", enum_type("supplier_part_status", lifecycle), nullable=False),
        sa.UniqueConstraint("supplier_id", "part_id", name="uq_fo_supplier_part"),
        sa.UniqueConstraint("supplier_id", "supplier_part_number", name="uq_fo_supplier_part_number"),
        sa.CheckConstraint("lead_time_days >= 0", name="ck_fo_lead_time_nonnegative"),
    )
    op.create_table(
        "fo_bom_items",
        *entity_columns(),
        sa.Column("vehicle_model_id", sa.String(36), sa.ForeignKey("fo_vehicle_models.id", ondelete="CASCADE"), nullable=False),
        sa.Column("part_id", sa.String(36), sa.ForeignKey("fo_parts.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 3), nullable=False),
        sa.Column("bom_version", sa.String(40), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date()),
        sa.UniqueConstraint("vehicle_model_id", "part_id", "bom_version", "effective_from", name="uq_fo_bom_item_effectivity"),
        sa.CheckConstraint("quantity > 0", name="ck_fo_bom_quantity_positive"),
        sa.CheckConstraint("effective_to IS NULL OR effective_to >= effective_from", name="ck_fo_bom_effective_dates"),
    )
    op.create_table(
        "fo_batches",
        *entity_columns(),
        sa.Column("batch_number", sa.String(80), nullable=False, unique=True),
        sa.Column("part_id", sa.String(36), sa.ForeignKey("fo_parts.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("supplier_id", sa.String(36), sa.ForeignKey("fo_suppliers.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("manufactured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True)),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("status", enum_type("batch_status", lifecycle), nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_fo_batch_quantity_positive"),
        sa.CheckConstraint("received_at IS NULL OR received_at >= manufactured_at", name="ck_fo_batch_received_after_manufactured"),
    )
    op.create_index("ix_fo_batches_part_supplier", "fo_batches", ["part_id", "supplier_id"])
    op.create_table(
        "fo_quality_issues",
        *entity_columns(),
        sa.Column("issue_number", sa.String(80), nullable=False, unique=True),
        sa.Column("title", sa.String(250), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", enum_type("quality_severity", ("LOW", "MEDIUM", "HIGH", "CRITICAL")), nullable=False),
        sa.Column("status", enum_type("quality_issue_status", ("OPEN", "INVESTIGATING", "CONTAINED", "CLOSED")), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(120), nullable=False),
    )
    op.create_table(
        "fo_quality_cases",
        *entity_columns(),
        sa.Column("case_number", sa.String(80), nullable=False, unique=True),
        sa.Column("title", sa.String(250), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("priority", enum_type("quality_case_priority", ("LOW", "MEDIUM", "HIGH", "URGENT")), nullable=False),
        sa.Column("status", enum_type("quality_case_status", ("OPEN", "INVESTIGATING", "ACTION_REQUIRED", "CLOSED")), nullable=False),
        sa.Column("owner", sa.String(120), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("closed_at IS NULL OR closed_at >= opened_at", name="ck_fo_case_closed_after_opened"),
    )
    op.create_table(
        "fo_inspection_records",
        *entity_columns(),
        sa.Column("inspection_number", sa.String(80), nullable=False, unique=True),
        sa.Column("batch_id", sa.String(36), sa.ForeignKey("fo_batches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("process_id", sa.String(36), sa.ForeignKey("fo_processes.id", ondelete="SET NULL")),
        sa.Column("inspection_type", sa.String(100), nullable=False),
        sa.Column("metric_name", sa.String(100), nullable=False),
        sa.Column("measured_value", sa.Numeric(18, 6), nullable=False),
        sa.Column("lower_limit", sa.Numeric(18, 6), nullable=False),
        sa.Column("upper_limit", sa.Numeric(18, 6), nullable=False),
        sa.Column("result", enum_type("inspection_result", ("PASS", "FAIL")), nullable=False),
        sa.Column("inspected_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("lower_limit <= upper_limit", name="ck_fo_inspection_limits"),
    )
    op.create_index("ix_fo_inspections_batch_result", "fo_inspection_records", ["batch_id", "result"])
    op.create_table(
        "fo_quality_issue_batches",
        *entity_columns(),
        sa.Column("quality_issue_id", sa.String(36), sa.ForeignKey("fo_quality_issues.id", ondelete="CASCADE"), nullable=False),
        sa.Column("batch_id", sa.String(36), sa.ForeignKey("fo_batches.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("quality_issue_id", "batch_id", name="uq_fo_issue_batch"),
    )
    op.create_table(
        "fo_quality_case_issues",
        *entity_columns(),
        sa.Column("quality_case_id", sa.String(36), sa.ForeignKey("fo_quality_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quality_issue_id", sa.String(36), sa.ForeignKey("fo_quality_issues.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("quality_case_id", "quality_issue_id", name="uq_fo_case_issue"),
    )
    op.create_table(
        "fo_corrective_actions",
        *entity_columns(),
        sa.Column("action_number", sa.String(80), nullable=False, unique=True),
        sa.Column("quality_case_id", sa.String(36), sa.ForeignKey("fo_quality_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(250), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("action_type", sa.String(100), nullable=False),
        sa.Column("status", enum_type("corrective_action_status", ("OPEN", "IN_PROGRESS", "COMPLETED", "CANCELLED")), nullable=False),
        sa.Column("assignee", sa.String(120), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("fo_corrective_actions")
    op.drop_table("fo_quality_case_issues")
    op.drop_table("fo_quality_issue_batches")
    op.drop_index("ix_fo_inspections_batch_result", table_name="fo_inspection_records")
    op.drop_table("fo_inspection_records")
    op.drop_table("fo_quality_cases")
    op.drop_table("fo_quality_issues")
    op.drop_index("ix_fo_batches_part_supplier", table_name="fo_batches")
    op.drop_table("fo_batches")
    op.drop_table("fo_bom_items")
    op.drop_table("fo_supplier_parts")
    op.drop_table("fo_processes")
    op.drop_table("fo_users")
    op.drop_table("fo_documents")
    op.drop_table("fo_plants")
    op.drop_table("fo_vehicle_models")
    op.drop_table("fo_parts")
    op.drop_table("fo_suppliers")

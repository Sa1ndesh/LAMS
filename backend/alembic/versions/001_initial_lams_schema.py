"""initial_lams_schema

Revision ID: 001_initial_lams_schema
Revises: 
Create Date: 2026-08-23 13:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001_initial_lams_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. roles
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("idx_roles_name", "roles", ["name"])

    # 2. states
    op.create_table(
        "states",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("idx_states_code", "states", ["code"])

    # 3. districts
    op.create_table(
        "districts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("state_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["state_id"], ["states.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("state_id", "code", name="uq_district_state_code"),
    )
    op.create_index("idx_districts_state_id", "districts", ["state_id"])

    # 4. users
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("state_id", sa.Integer(), nullable=True),
        sa.Column("district_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["state_id"], ["states.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["district_id"], ["districts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("idx_users_email", "users", ["email"])

    # 5. projects
    op.create_table(
        "projects",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("ministry", sa.String(length=255), nullable=False),
        sa.Column("implementing_agency", sa.String(length=255), nullable=False),
        sa.Column("state_id", sa.Integer(), nullable=False),
        sa.Column("district_id", sa.Integer(), nullable=False),
        sa.Column("village", sa.String(length=255), nullable=False),
        sa.Column("land_proposed_hectares", sa.Float(), nullable=False),
        sa.Column("land_acquired_hectares", sa.Float(), nullable=False),
        sa.Column("budget_inr", sa.Float(), nullable=False),
        sa.Column("current_stage", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("target_completion_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("land_proposed_hectares >= 0", name="chk_project_land_proposed_positive"),
        sa.CheckConstraint("land_acquired_hectares >= 0", name="chk_project_land_acquired_positive"),
        sa.CheckConstraint("budget_inr >= 0", name="chk_project_budget_positive"),
        sa.ForeignKeyConstraint(["state_id"], ["states.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["district_id"], ["districts.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_code"),
    )
    op.create_index("idx_projects_code", "projects", ["project_code"])
    op.create_index("idx_projects_state_id", "projects", ["state_id"])
    op.create_index("idx_projects_district_id", "projects", ["district_id"])
    op.create_index("idx_projects_stage", "projects", ["current_stage"])
    op.create_index("idx_projects_status", "projects", ["status"])

    # 6. land_parcels
    op.create_table(
        "land_parcels",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("parcel_code", sa.String(length=50), nullable=False),
        sa.Column("survey_number", sa.String(length=100), nullable=False),
        sa.Column("state_id", sa.Integer(), nullable=False),
        sa.Column("district_id", sa.Integer(), nullable=False),
        sa.Column("taluk", sa.String(length=100), nullable=False),
        sa.Column("village", sa.String(length=100), nullable=False),
        sa.Column("area_hectares", sa.Float(), nullable=False),
        sa.Column("land_type", sa.String(length=50), nullable=False),
        sa.Column("acquisition_status", sa.String(length=50), nullable=False),
        sa.Column("compensation_status", sa.String(length=50), nullable=False),
        sa.Column("possession_status", sa.String(length=50), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("area_hectares >= 0", name="chk_parcel_area_positive"),
        sa.CheckConstraint("latitude >= -90 AND latitude <= 90", name="chk_parcel_latitude_bounds"),
        sa.CheckConstraint("longitude >= -180 AND longitude <= 180", name="chk_parcel_longitude_bounds"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["state_id"], ["states.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["district_id"], ["districts.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("parcel_code"),
        sa.UniqueConstraint("project_id", "survey_number", name="uq_parcel_project_survey"),
    )
    op.create_index("idx_parcels_project_id", "land_parcels", ["project_id"])
    op.create_index("idx_parcels_survey", "land_parcels", ["survey_number"])
    op.create_index("idx_parcels_village", "land_parcels", ["village"])

    # 7. land_owners
    op.create_table(
        "land_owners",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("parcel_id", sa.String(length=36), nullable=False),
        sa.Column("owner_reference", sa.String(length=100), nullable=False),
        sa.Column("display_name", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["parcel_id"], ["land_parcels.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_owners_parcel_id", "land_owners", ["parcel_id"])

    # 8. compensation_records
    op.create_table(
        "compensation_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("parcel_id", sa.String(length=36), nullable=False),
        sa.Column("assessed_amount_inr", sa.Float(), nullable=False),
        sa.Column("approved_amount_inr", sa.Float(), nullable=False),
        sa.Column("disbursed_amount_inr", sa.Float(), nullable=False),
        sa.Column("payment_status", sa.String(length=50), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("assessed_amount_inr >= 0", name="chk_comp_assessed_positive"),
        sa.CheckConstraint("approved_amount_inr >= 0", name="chk_comp_approved_positive"),
        sa.CheckConstraint("disbursed_amount_inr >= 0", name="chk_comp_disbursed_positive"),
        sa.CheckConstraint("disbursed_amount_inr <= approved_amount_inr", name="chk_comp_disbursed_le_approved"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parcel_id"], ["land_parcels.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_comp_project_id", "compensation_records", ["project_id"])
    op.create_index("idx_comp_parcel_id", "compensation_records", ["parcel_id"])
    op.create_index("idx_comp_status", "compensation_records", ["payment_status"])

    # 9. affected_families
    op.create_table(
        "affected_families",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("family_reference_id", sa.String(length=50), nullable=False),
        sa.Column("village", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("is_affected", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_displaced", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("rr_status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("family_reference_id"),
    )
    op.create_index("idx_families_project_id", "affected_families", ["project_id"])
    op.create_index("idx_families_rr_status", "affected_families", ["rr_status"])

    # 10. rehabilitation_records
    op.create_table(
        "rehabilitation_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("family_id", sa.String(length=36), nullable=False),
        sa.Column("housing_assistance_status", sa.String(length=50), nullable=False),
        sa.Column("employment_assistance_status", sa.String(length=50), nullable=False),
        sa.Column("compensation_status", sa.String(length=50), nullable=False),
        sa.Column("resettlement_status", sa.String(length=50), nullable=False),
        sa.Column("completion_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["family_id"], ["affected_families.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_rehab_project_id", "rehabilitation_records", ["project_id"])
    op.create_index("idx_rehab_family_id", "rehabilitation_records", ["family_id"])

    # 11. documents
    op.create_table(
        "documents",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("document_name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("file_reference", sa.String(length=500), nullable=False),
        sa.Column("uploaded_by", sa.String(length=255), nullable=False),
        sa.Column("upload_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_documents_project_id", "documents", ["project_id"])
    op.create_index("idx_documents_category", "documents", ["category"])

    # 12. milestones
    op.create_table(
        "milestones",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("stage", sa.String(length=100), nullable=False),
        sa.Column("planned_date", sa.Date(), nullable=False),
        sa.Column("actual_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("delay_days", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_milestones_project_id", "milestones", ["project_id"])

    # 13. approvals
    op.create_table(
        "approvals",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("stage", sa.String(length=100), nullable=False),
        sa.Column("requested_by", sa.String(length=255), nullable=False),
        sa.Column("approved_by", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("remarks", sa.String(length=1000), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_approvals_project_id", "approvals", ["project_id"])

    # 14. notifications
    op.create_table(
        "notifications",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("project_id", sa.String(length=36), nullable=True),
        sa.Column("notification_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.String(length=1000), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_notifications_user_id", "notifications", ["user_id"])
    op.create_index("idx_notifications_project_id", "notifications", ["project_id"])

    # 15. audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("old_value", sa.JSON(), nullable=True),
        sa.Column("new_value", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_audit_user_id", "audit_logs", ["user_id"])
    op.create_index("idx_audit_entity", "audit_logs", ["entity_type", "entity_id"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("notifications")
    op.drop_table("approvals")
    op.drop_table("milestones")
    op.drop_table("documents")
    op.drop_table("rehabilitation_records")
    op.drop_table("affected_families")
    op.drop_table("compensation_records")
    op.drop_table("land_owners")
    op.drop_table("land_parcels")
    op.drop_table("projects")
    op.drop_table("users")
    op.drop_table("districts")
    op.drop_table("states")
    op.drop_table("roles")


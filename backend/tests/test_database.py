import pytest
from sqlalchemy import inspect
from app.models import (
    Base,
    Role,
    User,
    State,
    District,
    Project,
    LandParcel,
    LandOwner,
    CompensationRecord,
    AffectedFamily,
    RehabilitationRecord,
    Document,
    Milestone,
    Approval,
    Notification,
    AuditLog,
    UserRoleEnum,
    ProjectStageEnum,
    PaymentStatusEnum,
)


def test_model_tables_registered_in_metadata():
    """Verify that all 15 core domain models are registered in Base.metadata."""
    tables = Base.metadata.tables.keys()

    expected_tables = [
        "roles",
        "states",
        "districts",
        "users",
        "projects",
        "land_parcels",
        "land_owners",
        "compensation_records",
        "affected_families",
        "rehabilitation_records",
        "documents",
        "milestones",
        "approvals",
        "notifications",
        "audit_logs",
    ]

    for table_name in expected_tables:
        assert table_name in tables, f"Expected table '{table_name}' was not found in Base.metadata.tables"


def test_project_model_constraints():
    """Inspect Project model columns, primary key, and check constraints."""
    table = Base.metadata.tables["projects"]

    assert "id" in table.columns
    assert "project_code" in table.columns
    assert "land_proposed_hectares" in table.columns
    assert "budget_inr" in table.columns
    assert table.columns["project_code"].unique is True

    # Check constraint check
    constraints = [c.name for c in table.constraints if hasattr(c, "name")]
    assert "chk_project_land_proposed_positive" in constraints
    assert "chk_project_budget_positive" in constraints


def test_compensation_model_pending_calculation():
    """Test CompensationRecord pending_amount_inr dynamic property formula."""
    record = CompensationRecord(
        assessed_amount_inr=5000000.0,
        approved_amount_inr=5000000.0,
        disbursed_amount_inr=3000000.0,
        payment_status=PaymentStatusEnum.APPROVED,
    )

    assert record.pending_amount_inr == 2000000.0
    assert record.disbursed_amount_inr <= record.approved_amount_inr


def test_enums_integrity():
    """Test domain enum values."""
    assert UserRoleEnum.SUPER_ADMIN.value == "SUPER_ADMIN"
    assert ProjectStageEnum.PROPOSAL.value == "Proposal"
    assert PaymentStatusEnum.DISBURSED.value == "DISBURSED"


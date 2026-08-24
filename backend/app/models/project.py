import uuid
from datetime import date, datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Integer, Float, Date, DateTime, ForeignKey, Enum as SQLEnum, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, utc_now
from app.models.enums import (
    ProjectCategoryEnum,
    ProjectStageEnum,
    ProjectStatusEnum,
    MilestoneStatusEnum,
    ApprovalStatusEnum,
)

if TYPE_CHECKING:
    from app.models.geography import State, District
    from app.models.parcel import LandParcel
    from app.models.compensation import CompensationRecord
    from app.models.family import AffectedFamily, RehabilitationRecord
    from app.models.document import Document
    from app.models.notification import Notification


class Project(Base, TimestampMixin):
    __tablename__ = "projects"
    __table_args__ = (
        CheckConstraint("land_proposed_hectares >= 0", name="chk_project_land_proposed_positive"),
        CheckConstraint("land_acquired_hectares >= 0", name="chk_project_land_acquired_positive"),
        CheckConstraint("budget_inr >= 0", name="chk_project_budget_positive"),
        Index("idx_projects_code_state", "project_code", "state_id"),
        Index("idx_projects_stage_status", "current_stage", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[ProjectCategoryEnum] = mapped_column(SQLEnum(ProjectCategoryEnum, values_callable=lambda obj: [e.value for e in obj], native_enum=False), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    ministry: Mapped[str] = mapped_column(String(255), nullable=False)
    implementing_agency: Mapped[str] = mapped_column(String(255), nullable=False)

    state_id: Mapped[int] = mapped_column(Integer, ForeignKey("states.id", ondelete="RESTRICT"), nullable=False, index=True)
    district_id: Mapped[int] = mapped_column(Integer, ForeignKey("districts.id", ondelete="RESTRICT"), nullable=False, index=True)
    village: Mapped[str] = mapped_column(String(255), nullable=False)

    land_proposed_hectares: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    land_acquired_hectares: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    budget_inr: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    current_stage: Mapped[ProjectStageEnum] = mapped_column(SQLEnum(ProjectStageEnum, values_callable=lambda obj: [e.value for e in obj], native_enum=False), nullable=False, default=ProjectStageEnum.PROPOSAL, index=True)
    status: Mapped[ProjectStatusEnum] = mapped_column(SQLEnum(ProjectStatusEnum, values_callable=lambda obj: [e.value for e in obj], native_enum=False), nullable=False, default=ProjectStatusEnum.ACTIVE, index=True)

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    target_completion_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Relationships
    state: Mapped["State"] = relationship("State", back_populates="projects")
    district: Mapped["District"] = relationship("District", back_populates="projects")

    land_parcels: Mapped[List["LandParcel"]] = relationship("LandParcel", back_populates="project", cascade="all, delete-orphan")
    compensation_records: Mapped[List["CompensationRecord"]] = relationship("CompensationRecord", back_populates="project", cascade="all, delete-orphan")
    affected_families: Mapped[List["AffectedFamily"]] = relationship("AffectedFamily", back_populates="project", cascade="all, delete-orphan")
    rehabilitation_records: Mapped[List["RehabilitationRecord"]] = relationship("RehabilitationRecord", back_populates="project", cascade="all, delete-orphan")
    documents: Mapped[List["Document"]] = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    milestones: Mapped[List["Milestone"]] = relationship("Milestone", back_populates="project", cascade="all, delete-orphan")
    approvals: Mapped[List["Approval"]] = relationship("Approval", back_populates="project", cascade="all, delete-orphan")
    notifications: Mapped[List["Notification"]] = relationship("Notification", back_populates="project", cascade="all, delete-orphan")


class Milestone(Base, TimestampMixin):
    __tablename__ = "milestones"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    stage: Mapped[str] = mapped_column(String(100), nullable=False)

    planned_date: Mapped[date] = mapped_column(Date, nullable=False)
    actual_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[MilestoneStatusEnum] = mapped_column(SQLEnum(MilestoneStatusEnum, values_callable=lambda obj: [e.value for e in obj], native_enum=False), nullable=False, default=MilestoneStatusEnum.PENDING)
    delay_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    project: Mapped["Project"] = relationship("Project", back_populates="milestones")


class Approval(Base, TimestampMixin):
    __tablename__ = "approvals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    stage: Mapped[str] = mapped_column(String(100), nullable=False)

    requested_by: Mapped[str] = mapped_column(String(255), nullable=False)
    approved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[ApprovalStatusEnum] = mapped_column(SQLEnum(ApprovalStatusEnum, values_callable=lambda obj: [e.value for e in obj], native_enum=False), nullable=False, default=ApprovalStatusEnum.PENDING)
    remarks: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped["Project"] = relationship("Project", back_populates="approvals")
